"""Demo data seeding for CRM-server SQLite database."""

import aiosqlite


async def seed_data(db: aiosqlite.Connection) -> None:
    """Insert demo seed data. Uses INSERT OR IGNORE to be idempotent."""

    # --- Customers (TMF629) ---
    await db.executemany(
        "INSERT OR IGNORE INTO customers (id, phone, name, customer_category, product_name) VALUES (?, ?, ?, ?, ?)",
        [
            ("cust_001", "13800000001", "Alice Wang", "gold", "Plan-50G"),
            ("cust_002", "13800000002", "Bob Li", "silver", "Plan-100G"),
            ("cust_003", "13800000003", "Carol Zhang", "bronze", "Plan-200G"),
        ],
    )

    # --- Product Offerings (TMF620) ---
    await db.executemany(
        "INSERT OR IGNORE INTO product_offerings (id, name, description, price, price_unit) VALUES (?, ?, ?, ?, ?)",
        [
            ("po_001", "Plan-50G", "Basic 50GB data plan with unlimited calls", 49.0, "EUR"),
            ("po_002", "Plan-100G", "Standard 100GB data plan with unlimited calls and SMS", 99.0, "EUR"),
            ("po_003", "Plan-200G", "Premium 200GB data plan with unlimited calls, SMS, and roaming", 149.0, "EUR"),
            ("po_004", "Plan-500G", "Ultimate 500GB data plan with all premium features", 199.0, "EUR"),
            ("po_005", "Plan-Unlimited", "Unlimited data plan with priority network access", 299.0, "EUR"),
        ],
    )

    # --- Identity Verification Records (TMF720) ---
    # Customer A: verified (passing OTP check)
    # Customer B: verified (passing biometric check)
    # Customer C: not verified (simulated fraud flag)
    await db.executemany(
        "INSERT OR IGNORE INTO identities (id, customer_id, verified, confidence_score, verified_at) VALUES (?, ?, ?, ?, ?)",
        [
            ("ident_001", "cust_001", 1, 0.95, "2026-03-14T10:00:00Z"),
            ("ident_002", "cust_002", 1, 0.88, "2026-03-14T10:00:00Z"),
            ("ident_003", "cust_003", 0, 0.20, "2026-03-14T10:00:00Z"),
        ],
    )

    # --- AI Models (TMF915) ---
    await db.executemany(
        "INSERT OR IGNORE INTO ai_models (id, model_name, version, status, accuracy_score, last_updated) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("qwen2.5_7b", "qwen2.5:7b", "7b", "active", 0.87, "2026-03-01T00:00:00Z"),
        ],
    )

    await db.commit()
