---
published: false
title: 'When (not) to review code'
cover_image: 'https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO/master/blog-posts/NAME-OF-YOUR-BLOG-POST/assets/your-asset.png'
description: 'Description of the article'
tags: tag1, tag2, tag3
series:
canonical_url:
---

* __Peer-review:__ another human other than the author reviews the code.
* __Self-review:__ the author reviews the code before publicizing it.

## When (not) to review

* Don't make human reviews mandatory.
* In a foreign codebase, awaiting codeowner review is how to be a good
  neighbour.
* AI-generated code must be reviewed. Self-review is sufficient if you know the
  codebase, peer-review otherwise.
* Self-review is enough to merge.
* A PR can be reviewed after merge.
* Bigger changes should be reviewed? The big change should be discussed before
  the work is started.
* Only don't merge - if you have a reason not to merge.
  * The change is a one-way door.
  * Changes that touch a lot of files. A-lot-of-files changes become hard to
    revert when they are of such nature that subsequent work would immdiately
    base on those files. Such changes are therefore to be considered as a
    one-way-door.
  * The change is significant and has not been discussed with anyone.
  * There are multiple ways to solve the problem and you want to see what
    somebody else thinks of the approach you chose.

This way of working requires two things:

* Apply judgement and caution -- don't make anyone regret the decision.
* Trust your team mates to do good work and apply judgement.

## How to review

* __Only block the PR if you have a reason to block the PR__
  * One-way-door changes that aren't in an acceptable state
  * Leave a lot of comments but approve the PR -- let the author choose to defer
    the changes you request to a follow-up PR.
  * Don't leave a lot of comments. Approve the PR and make your changes
    yourselves later. You want the author to take note of your changes, send
    them the PR (but don't require their review 😉)

## But

### But what about Juniors -- they need feedback to learn the craft

Yup and you can provide that feedback in a PR review even after the merge has
happened.
