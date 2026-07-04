# docs/submission-kit

Assets and checklists for the hackathon submission.

## Blog journal (Blog Post Award)

We document the build as we go, and the journal drafts itself: [`blogger.py`](blogger.py)
feeds our own `HACKATHON.md` + `git log` to `qwen-plus` (the same Qwen spine the agents
call at runtime) and writes a Markdown draft, which we then hand-edit.

```sh
python docs/submission-kit/blogger.py          # regenerate the draft from current repo activity
python docs/submission-kit/blogger.py --check  # offline self-check, no API call
```

Latest edited post: [`blog-draft.md`](blog-draft.md). Re-run after each real milestone
lands in `HACKATHON.md`, then edit and publish the next part. The prompt's hard rule is
"invent nothing that isn't in the inputs," so the post stays honest as the log grows.

## Track 3 Submission Pack

- [Devpost draft and demo script](git-committer-devpost.md)
- [Architecture diagram](../architecture/git-committer-track3.md)
- [Alibaba Cloud ECS proof file](../../agents/git-committer/deploy.py)

## Planned Contents

- Demo video script and storyboard
- Screenshot pack (one per agent, one system overview)
- Deployment proof screenshots / URLs
- Submission form answers (draft)

See [../../HACKATHON.md](../../HACKATHON.md) for the per-track update log and submission links.
