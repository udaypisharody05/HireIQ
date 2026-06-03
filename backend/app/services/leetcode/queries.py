USER_PROFILE_STATS_QUERY = """
query UserProfileStats($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
      reputation
    }
    submitStatsGlobal {
      acSubmissionNum {
        difficulty
        count
      }
    }
  }
}
"""

RECENT_ACCEPTED_SUBMISSIONS_QUERY = """
query RecentAcceptedSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
  }
}
"""

PROBLEM_METADATA_QUERY = """
query ProblemMetadata($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId
    title
    titleSlug
    difficulty
    acRate
    topicTags {
      name
      slug
    }
  }
}
"""
