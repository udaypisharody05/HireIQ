from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from socket import timeout as SocketTimeout
from typing import Any

from app.services.leetcode.queries import (
    PROBLEM_METADATA_QUERY,
    RECENT_ACCEPTED_SUBMISSIONS_QUERY,
    USER_PROFILE_STATS_QUERY,
)

logger = logging.getLogger(__name__)


class LeetCodeClientError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class LeetCodeClient:
    endpoint = "https://leetcode.com/graphql"

    def __init__(self, timeout_seconds: int = 10, max_attempts: int = 2, retry_delay_seconds: float = 0.5) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.retry_delay_seconds = retry_delay_seconds

    def get_profile_stats(self, username: str) -> dict[str, Any]:
        data = self._execute("UserProfileStats", USER_PROFILE_STATS_QUERY, {"username": username})
        matched_user = data.get("matchedUser")
        if matched_user is None:
            raise LeetCodeClientError("LeetCode user was not found.", status_code=502)
        if not isinstance(matched_user, dict):
            raise LeetCodeClientError("LeetCode profile response had an unexpected shape.")
        return matched_user

    def get_recent_accepted_submissions(self, username: str, limit: int = 50) -> list[dict[str, Any]]:
        data = self._execute("RecentAcceptedSubmissions", RECENT_ACCEPTED_SUBMISSIONS_QUERY, {"username": username, "limit": limit})
        submissions = data.get("recentAcSubmissionList")
        if not isinstance(submissions, list):
            raise LeetCodeClientError("LeetCode submissions response had an unexpected shape.")
        return [submission for submission in submissions if isinstance(submission, dict)]

    def get_problem_metadata(self, title_slug: str) -> dict[str, Any]:
        data = self._execute("ProblemMetadata", PROBLEM_METADATA_QUERY, {"titleSlug": title_slug})
        question = data.get("question")
        if question is None:
            raise LeetCodeClientError(f"LeetCode problem metadata was not found for slug '{title_slug}'.")
        if not isinstance(question, dict):
            raise LeetCodeClientError("LeetCode problem metadata response had an unexpected shape.")
        return question

    def _execute(self, operation_name: str, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "HireIQ/0.1",
        }

        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            request = urllib.request.Request(self.endpoint, data=payload, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    response_body = response.read().decode("utf-8")
                    decoded = json.loads(response_body)
                    return self._extract_data(decoded, operation_name, variables)
            except (SocketTimeout, TimeoutError) as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    raise LeetCodeClientError("LeetCode request timed out.", status_code=503) from exc
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code >= 500 and attempt < self.max_attempts:
                    time.sleep(self.retry_delay_seconds)
                    continue
                status_code = 503 if exc.code in {403, 429, 503} else 502
                raise LeetCodeClientError(f"LeetCode returned HTTP {exc.code}.", status_code=status_code) from exc
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    raise LeetCodeClientError("LeetCode request failed.", status_code=503) from exc
            except json.JSONDecodeError as exc:
                raise LeetCodeClientError("LeetCode returned invalid JSON.") from exc

            time.sleep(self.retry_delay_seconds)

        raise LeetCodeClientError("LeetCode request failed.", status_code=503) from last_error

    @staticmethod
    def _extract_data(decoded: Any, operation_name: str, variables: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(decoded, dict):
            raise LeetCodeClientError("LeetCode returned an unexpected response.")

        errors = decoded.get("errors")
        if errors:
            error_message = _format_graphql_errors(errors)
            logger.error(
                "LeetCode GraphQL error during %s with variables %s: %s",
                operation_name,
                variables,
                error_message,
            )
            raise LeetCodeClientError(f"LeetCode GraphQL returned errors: {error_message}")

        data = decoded.get("data")
        if not isinstance(data, dict):
            raise LeetCodeClientError("LeetCode GraphQL response did not include data.")

        return data


def _format_graphql_errors(errors: Any) -> str:
    if not isinstance(errors, list):
        return str(errors)

    messages: list[str] = []
    for error in errors:
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message:
                messages.append(message)
                continue
        messages.append(str(error))

    return "; ".join(messages) if messages else "Unknown GraphQL error."
