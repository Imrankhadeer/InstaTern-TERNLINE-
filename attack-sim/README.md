# InstaTern & Cyber Engine — Automated Adversary Attack Simulator

Automated red-team emulation suite designed to launch realistic, multi-stage attacks against `InstaTern` and verify the real-time detection, correlation, and active containment capabilities of `Cyber Engine`.

---

## 🚀 Attacks Included

1. **Credential Stuffing & Password Spraying (`T1110.001`)**
   - High-speed credential spray against user accounts from blacklisted attacker IPs.
   - Triggers Fast-Track brute force rules (`detector.auth.brute_force`).

2. **Stealth Infiltration & Token Harvesting (`T1550.002`)**
   - Authenticates through anonymous proxy IPs, harvests JWT bearer tokens, and maps private creator profiles.

3. **Multi-Stage Cross-Service Exfiltration Chain (`T1048` & `T1005`)**
   - Chains search fuzzing, mass feed dumps, and database extraction patterns across services.

4. **Bot Swarm & Rapid Follow Churn (`T1078`)**
   - Automated registration of synthetic bot accounts and high-frequency follow/unfollow flooding.

5. **Direct Distributed Trace Injection**
   - Injects correlated multi-service trace sequences (`api-service` -> `worker-service` -> `database-service`) directly into the engine.

---

## 👥 Normal User Baseline Traffic Simulator

An interactive CLI tool to generate organic, benign user activity (ideal for testing baselines and verifying normal user interactions against the Instagram application):

### 1. Launch Interactive Menu Mode (Select & Choose)
Simply run the script with no arguments:
```bash
python user_sim.py
```
Or specify your remote target URL:
```bash
python user_sim.py --target https://myapp-v1-p9qy.onrender.com
```

This presents an interactive terminal menu:
```text
=================================================================
   📸 INSTAGRAM APP - NORMAL USER ACTIVITY SIMULATOR
   Target URL: https://myapp-v1-p9qy.onrender.com
=================================================================

[Step 1] Select User Account to Login:
  [1] @sarah_dev (Sarah Developer)
  [2] @marcus_photo (Marcus Photographer)
  [3] @emily_style (Emily Style)
  [4] @alex_travels (Alex Travels)
  [5] Enter Custom Username

[Step 2] Choose Actions:
  [1] Full Organic Session (Stories, Feed, Like, Comment, Search, DM)
  [2] Browse Feed (View recent posts)
  [3] Watch Active Stories
  [4] Like a Post
  [5] Comment on a Post
  [6] Search (Hashtags or Creators)
  [7] Follow a Creator
  [8] Send a Direct Message
  [9] Publish a New Photo Post
  [10] Switch User
  [11] Continuous Background Traffic Loop
  [12] Exit
```

### 2. Scripting / Non-Interactive Flags
```bash
# Full automated user routine:
python user_sim.py --action session --user sarah_dev

# Browse feed only:
python user_sim.py --action feed

# Search:
python user_sim.py --action search --query photography

# Send a direct message:
python user_sim.py --action dm --recipient marcus_photo --text "Hey, how are you?"

# Continuous automated background traffic:
python user_sim.py --loop --interval 10
```

---

## 🛠️ Usage

### Run All Attack Scenarios:
```bash
python attack.py
```

### Attack a Remote Deployment (e.g., Render):
```bash
python attack.py --target https://myapp-v1-p9qy.onrender.com/?chat=emily_style --engine https://ternline.vercel.app
```

### Run Specific Attack Scenario:
```bash
python attack.py --scenario brute_force
python attack.py --scenario harvesting
python attack.py --scenario exfil
python attack.py --scenario swarm
python attack.py --scenario direct
```
