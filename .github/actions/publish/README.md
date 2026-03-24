# Using KCP GitHub Action

Publish knowledge artifacts from your CI/CD workflows.

## Example: Publish release notes

```yaml
name: Release

on:
  release:
    types: [published]

jobs:
  publish-to-kcp:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Publish release notes to KCP
        uses: kcp-protocol/kcp/.github/actions/publish@main
        with:
          peer_url: https://peer01.kcp-protocol.org
          title: "Release ${{ github.event.release.tag_name }}"
          content: ${{ github.event.release.body }}
          format: markdown
          tags: release,changelog,${{ github.repository }}
          visibility: public
          source: github-releases
```

## Example: Publish test results

```yaml
- name: Run tests
  run: npm test -- --json --outputFile=test-results.json
  
- name: Publish test results to KCP
  if: always()
  uses: kcp-protocol/kcp/.github/actions/publish@main
  with:
    peer_url: https://peer01.kcp-protocol.org
    title: "Test Results - ${{ github.sha }}"
    content: ${{ steps.test.outputs.results }}
    format: json
    tags: tests,ci,${{ github.repository }}
    visibility: org
```

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `peer_url` | ✅ | - | KCP peer URL |
| `title` | ✅ | - | Artifact title |
| `content` | ✅ | - | Artifact content |
| `format` | ❌ | `text` | `markdown`, `text`, `json`, `html`, `csv`, `yaml` |
| `tags` | ❌ | `` | Comma-separated tags |
| `visibility` | ❌ | `public` | `public`, `org`, `team`, `private` |
| `source` | ❌ | `github-actions` | Source identifier |

## Outputs

| Output | Description |
|--------|-------------|
| `artifact_id` | Published artifact UUID |
| `artifact_url` | Full artifact URL |

## Requirements

- Public peer URL (e.g., `https://peer01.kcp-protocol.org`)
- No authentication required for `public` visibility
- Requires GitHub-hosted runner (curl + jq available)
