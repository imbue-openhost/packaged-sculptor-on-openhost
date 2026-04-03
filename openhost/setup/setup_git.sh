#!/bin/bash
# Configure git identity and credentials from secrets.
# Sources /run/openhost-secrets.env for GIT_USER_NAME, GIT_USER_EMAIL, GITHUB_ACCESS_TOKEN, GITLAB_ACCESS_TOKEN.
set -e

source /run/openhost-secrets.env

if [ -z "$GIT_USER_NAME" ] || [ -z "$GIT_USER_EMAIL" ]; then
    echo "setup_git: GIT_USER_NAME or GIT_USER_EMAIL not available, skipping"
    exit 0
fi

git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"
git config --global core.editor vim
git config --global push.default simple
git config --global credential.helper store

echo "setup_git: configured for $GIT_USER_NAME <$GIT_USER_EMAIL>"

# Store credentials for GitHub and GitLab separately
> ~/.git-credentials
if [ -n "$GITHUB_ACCESS_TOKEN" ]; then
    echo "https://${GITHUB_ACCESS_TOKEN}@github.com" >> ~/.git-credentials
    echo "setup_git: credentials stored for github.com"
fi
if [ -n "$GITLAB_ACCESS_TOKEN" ]; then
    echo "https://oauth2:${GITLAB_ACCESS_TOKEN}@gitlab.com" >> ~/.git-credentials
    echo "setup_git: credentials stored for gitlab.com"
fi
if [ -s ~/.git-credentials ]; then
    chmod 600 ~/.git-credentials
else
    rm -f ~/.git-credentials
    echo "setup_git: no access tokens, skipping credentials"
fi
