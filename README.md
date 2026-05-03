# Project 6 — Staging and Production Environments with Approval Gate

Automated deployment pipeline with full environment separation — every push deploys to staging automatically, production requires a manual approval before anything ships to real users.

---

## The Problem This Solves

Most early-stage teams deploy directly to production. Every push is a gamble — if something breaks, real users are affected immediately and the team is scrambling to fix a live system under pressure. There is no safe place to catch failures before they matter. This project solves that: two isolated environments where staging acts as a replica of production, every push lands there first, and a human approval gate ensures nothing reaches real users until someone has verified it works.

---

## What Was Built

- **Two isolated AWS EC2 instances** — one for staging, one for production — each with its own SSH key pair and credentials
- **GitHub Environments** with isolated secret namespaces — staging and production credentials never share the same namespace
- **Manual approval gate** on the production environment — pipeline pauses and waits for a designated reviewer before deploying
- **Docker image built once, deployed identically to both environments** — staging and production are guaranteed to run the exact same artifact
- **Git SHA image tagging** — every build is traceable to the exact commit that produced it, enabling precise rollback
- **Health check after every deploy** — `curl` verifies the app is responding before the pipeline reports success
- **Full four-job pipeline** — test → build-and-push → deploy-staging → deploy-production

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│  ┌────────┐   ┌────────────────┐                           │
│  │  test  │──▶│ build-and-push │                           │
│  └────────┘   └───────┬────────┘                           │
│                        │                                   │
│          ┌─────────────┴──────────────┐                    │
│          ▼                            ▼                    │
│  ┌───────────────┐          ┌──────────────────────┐       │
│  │ deploy-staging│          │  deploy-production   │       │
│  │  (automatic)  │          │ (approval required)  │       │
│  └───────┬───────┘          └─────────┬────────────┘       │
└──────────┼───────────────────────────┼─────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────┐         ┌──────────────────────┐
│  Staging EC2    │         │    Production EC2    │
│                 │         │                      │
│ Flask + Postgres│         │  Flask + Postgres    │
│     :5001       │         │      :5001           │
└─────────────────┘         └──────────────────────┘
           ▲                           ▲
           └───────────┬───────────────┘
                       │
                  Docker Hub
     vimukthirandunu/ci-cd-project-6:<git-sha>
          (same image pulled by both EC2s)
```

Flask finds Postgres by the DNS name `db` — Docker's internal DNS resolves container names to IPs automatically inside each environment.

---

## Pipeline Structure

```
push to main
     │
     ▼
┌─────────┐
│  test   │  Spins up Postgres service container on the runner.
│         │  Sets DB credentials from GitHub Secrets.
│         │  Runs pytest against the Flask application.
│         │  Fails fast — nothing builds if tests fail.
└────┬────┘
     │ needs: test
     ▼
┌──────────────────┐
│ build-and-push   │  Builds Flask Docker image on the runner.
│                  │  Tags it with the full Git commit SHA.
│                  │  Pushes to Docker Hub.
│                  │  Outputs the SHA tag for downstream jobs.
└────────┬─────────┘
         │ needs: build-and-push
         │
         ├──────────────────────────────┐
         ▼                              ▼
┌─────────────────┐           ┌──────────────────────┐
│ deploy-staging  │           │  deploy-production   │
│                 │           │                      │
│ Targets staging │           │ Targets production   │
│ environment.    │           │ environment.         │
│ Uses staging    │           │ PAUSES — waits for   │
│ secrets.        │           │ manual approval.     │
│ SSHes into      │           │ Uses production      │
│ staging EC2.    │           │ secrets.             │
│ Pulls SHA image.│           │ SSHes into prod EC2. │
│ Health check.   │           │ Pulls same SHA image.│
└─────────────────┘           │ Health check.        │
                              └──────────────────────┘
```

**Why four jobs, not two?** Build once, deploy everywhere. The image is built on a clean GitHub runner and pushed to Docker Hub — both EC2s pull from there. This guarantees both environments run identical code. Separating build from deploy also makes failures easier to diagnose: if staging fails, production never runs.

---

## Key Technical Decisions

**1 — One image built once, deployed to both environments**
The build job runs once and produces a single Docker image tagged with the Git SHA. Both staging and production pull that exact tag from Docker Hub. This guarantees environment parity — the code reviewed on staging is byte-for-byte identical to what ships to production. Building separately per environment would introduce a gap where the two could silently diverge.

**2 — GitHub Environments as isolated secret namespaces**
Rather than naming secrets `STAGING_EC2_HOST` and `PROD_EC2_HOST` at the repo level, each environment gets its own isolated secret namespace. A job declares `environment: staging` or `environment: production` and receives the correct credentials automatically. This scales cleanly as secrets grow and makes it structurally impossible for a staging job to access production credentials.

**3 — SHA tagging over `latest`**
Every image is tagged with the full Git commit SHA rather than overwriting a `latest` tag. This makes every deployment traceable — you can look at a running container and know exactly which commit produced it. It also enables precise rollback: redeploying a previous SHA is deterministic and requires no guesswork about what `latest` currently points to.

---

## Local Setup

```bash
git clone https://github.com/Vimukthi-Randunu/ci-cd-project-6.git
cd ci-cd-project-6

# Create .env with local credentials
echo "POSTGRES_USER=flask_user
POSTGRES_PASSWORD=localpassword
POSTGRES_DB=flask_db
IMAGE_TAG=local" > .env

# Start the full system
docker compose up --build
```

API available at `http://localhost:5001`

---

## Part of a Progressive CI/CD Learning Series

This is Project 6 in a series building toward production-grade CI/CD systems:

- **Project 1** — GitHub Actions CI with Jest tests
- **Project 2** — Full CD to EC2 with health checks and rollback
- **Project 3** — Language-agnostic CI/CD with Python Flask
- **Project 4** — Containerization with Docker, image tagging with Git SHA
- **Project 5** — Multi-container systems, Docker networking, Compose orchestration
- **Project 6** — Staging and production environments, approval gates, environment separation ← this project
