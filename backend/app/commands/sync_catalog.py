from app.db.session import SessionLocal
from app.services.catalog_sync import CatalogSyncError, sync_problem_catalog


def main() -> int:
    with SessionLocal() as db:
        try:
            result = sync_problem_catalog(db)
        except CatalogSyncError as exc:
            print(f"Catalog sync failed: {exc}")
            return 1

    print(
        "Catalog sync completed: "
        f"{result.imported_count} imported, "
        f"{result.skipped_count} skipped, "
        f"{result.created_count} created, "
        f"{result.updated_count} updated, "
        f"{result.deactivated_count} deactivated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
