import os
import psycopg2
from dotenv import load_dotenv

# Load the environmental variables (RENDER_DB_URL)
load_dotenv()


def get_database_url():
    url = (
        os.getenv("DATABASE_URL")
        or os.getenv("RENDER_DB_URL")
        or os.getenv("RENDER_INTERNAL_DATABASE_URL")
    )
    if not url:
        raise RuntimeError(
            "Set DATABASE_URL, RENDER_DB_URL, or RENDER_INTERNAL_DATABASE_URL "
            "(external URL for local dev; internal only from Render’s private network)."
        )
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


def init_db():
    print("Connecting to secure Render PostgreSQL Database...")
    try:
        conn = psycopg2.connect(get_database_url())
        cur = conn.cursor()
        
        # 1. Create Core Platform Users Table
        print("Migrating User Schema...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS platform_users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                user_type VARCHAR(50) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # 2. Create Company Verification Data Table
        print("Migrating Corporate Table...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS company_profiles (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES platform_users(id) ON DELETE CASCADE,
                company_name VARCHAR(255) NOT NULL,
                gst_number VARCHAR(100),
                industry VARCHAR(100),
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 3. Create Home Feed Structural Data
        print("Migrating Social Feed Analytics Mode...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS feed_posts (
                id SERIAL PRIMARY KEY,
                author_email VARCHAR(255) NOT NULL,
                author_name VARCHAR(100),
                author_role VARCHAR(150),
                content TEXT NOT NULL,
                likes_count INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        
        # 4. Jobs Board
        print("Migrating Jobs Portal...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS jobs_board (
                id SERIAL PRIMARY KEY,
                role_title VARCHAR(255) NOT NULL,
                company_name VARCHAR(255) NOT NULL,
                location VARCHAR(100),
                tier VARCHAR(50), 
                salary VARCHAR(100),
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 5. Venture Deals
        print("Migrating Venture Funding Tables...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS venture_deals (
                id SERIAL PRIMARY KEY,
                startup_name VARCHAR(255) NOT NULL,
                round_type VARCHAR(100) NOT NULL,
                capital_raised VARCHAR(50),
                target_capital VARCHAR(50),
                domain_tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 6. B2B Services
        print("Migrating Services Directory...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS b2b_services (
                id SERIAL PRIMARY KEY,
                agency_name VARCHAR(255) NOT NULL,
                service_domain VARCHAR(150),
                starting_price VARCHAR(100),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 6b. Procurement (RFP) requests from buyers
        print("Migrating Procurement Requests...")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS procurement_requests (
                id SERIAL PRIMARY KEY,
                buyer_email VARCHAR(255),
                budget VARCHAR(150),
                vendor_tier VARCHAR(150),
                description TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )

        # 7. Core Wallets System
        print("Migrating Platform Wallets...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) UNIQUE NOT NULL,
                balance INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 8. Immutable Transaction Ledger
        print("Migrating Transaction Ledgers...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS wallet_transactions (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                amount INTEGER NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                description VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 9. Events Marketplace
        print("Migrating Event Ticketing System...")
        cur.execute('''
            CREATE TABLE IF NOT EXISTS platform_events (
                id SERIAL PRIMARY KEY,
                event_name VARCHAR(255) NOT NULL,
                host_name VARCHAR(255) NOT NULL,
                event_date VARCHAR(100),
                ticket_cost INTEGER DEFAULT 0,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Provide Mock Data Seed for Unified Experience
        cur.execute("SELECT COUNT(*) FROM jobs_board;")
        if cur.fetchone()[0] == 0:
            print("Seeding Initial Unified DB Metrics...")
            cur.execute(
                """
                INSERT INTO jobs_board (role_title, company_name, location, tier, salary, tags) VALUES
                ('Senior Cloud Architect', 'Nexus Solutions', 'Remote (Global)', 'Enterprise', '$140k - $160k', 'AWS, Kubernetes'),
                ('Lead Product Designer', 'MetaSphere', 'Hybrid - NY', 'Scale-up', '$120k + Equity', 'Figma, UI/UX');
                """
            )
            cur.execute(
                """
                INSERT INTO venture_deals (startup_name, round_type, capital_raised, target_capital, domain_tags) VALUES
                ('Aegis Security Networks', 'Series A', '$4.2M', '$10M', 'Cybersecurity, B2B SaaS'),
                ('Solflare Logistics', 'Seed Round', '$800k', '$2M', 'Supply Chain, AI Optimization');
                """
            )
            cur.execute(
                """
                INSERT INTO b2b_services (agency_name, service_domain, starting_price, description) VALUES
                ('Oktava Marketing', 'B2B Lead Generation', '$2,500/mo', 'Guaranteed MQL conversions through LinkedIn pipeline algorithms.'),
                ('Vanguard Legal', 'Corporate Restructuring', '$500/hr', 'Full-stack legal advisors for Series A startups.');
                """
            )
            cur.execute(
                """
                INSERT INTO platform_events (event_name, host_name, event_date, ticket_cost, description) VALUES
                ('Tech Founders Summit 2026', 'Y Combinator Alumni', 'Oct 15, 2026', 150, 'Exclusive networking and pitch deck teardowns for Seed to Series A startup leaders.'),
                ('Web3 Architecture Deep Dive', 'Solana Foundation', 'Nov 2, 2026', 250, 'Advanced protocol level security architecture patterns for decentralized exchanges.');
                """
            )
        
        # Commit configurations natively to Render
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Live Render Database Initialization Complete! All tables strictly defined.")

    except Exception as e:
        print(f"❌ Migration Error: {e}")

if __name__ == "__main__":
    init_db()
