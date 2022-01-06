const core = require('@actions/core');
const exec = require('@actions/exec');
const github = require('@actions/github');
const AdmZip = require('adm-zip');
const filesize = require('filesize');
const pathname = require('path');
const fs = require('fs');
const { throttling } = require('@octokit/plugin-throttling');
const { GitHub } = require('@actions/github/lib/utils');
const Util = require('util');
const Stream = require('stream');

async function getGoodArtifacts(client, owner, repo, releaseId, name) {
    console.log(`==> GET /repos/${owner}/${repo}/releases/${releaseId}/assets`);
    const goodRepoArtifacts = await client.paginate(
        "GET /repos/{owner}/{repo}/releases/{release_id}/assets",
        {
            owner: owner,
            repo: repo,
            release_id: releaseId,
            per_page: 100,
        },
        (releaseAssets, done) => {
            console.log(" ==> releaseAssets", releaseAssets);
            const goodAssets = releaseAssets.data.filter((a) => {
                console.log("==> Asset check", a);
                return a.name == name
            });
            if (goodAssets.length > 0) {
                done();
            }
            return goodAssets;
        }
    );

    console.log("==> maybe goodRepoArtifacts:", goodRepoArtifacts);
    return goodRepoArtifacts;
}

async function main() {
    try {
        const token = core.getInput("github_token", { required: true });
        const [owner, repo] = core.getInput("repo", { required: true }).split("/");
        const path = core.getInput("path", { required: true });
        const name = core.getInput("name");
        const download = core.getInput("download");
        const releaseTag = core.getInput("release-tag");
        const OctokitWithThrottling = GitHub.plugin(throttling);
        const client = new OctokitWithThrottling({
            auth: token,
            throttle: {
                onRateLimit: (retryAfter, options) => {
                    console.log(
                        `Request quota exhausted for request ${options.method} ${options.url}`
                    );

                    // Retry twice after hitting a rate limit error, then give up
                    if (options.request.retryCount <= 2) {
                        console.log(`Retrying after ${retryAfter} seconds!`);
                        return true;
                    } else {
                        console.log("Exhausted 2 retries");
                        core.setFailed("Exhausted 2 retries");
                    }
                },
                onAbuseLimit: (retryAfter, options) => {
                    // does not retry, only logs a warning
                    console.log(
                        `Abuse detected for request ${options.method} ${options.url}`
                    );
                    core.setFailed(`GitHub REST API Abuse detected for request ${options.method} ${options.url}`)
                },
            },
        });
        console.log("==> Repo:", owner + "/" + repo);

        const releaseInfo = await client.repos.getReleaseByTag({
            owner,
            repo,
            tag: releaseTag,
        });
        console.log(`==> Release info for tag ${releaseTag} = ${JSON.stringify(releaseInfo.data, null, 2)}`);
        const releaseId = releaseInfo.data.id;

        const goodArtifacts = await getGoodArtifacts(client, owner, repo, releaseId, name);
        console.log("==> goodArtifacts:", goodArtifacts);

        const artifactStatus = goodArtifacts.length === 0 ? "missing" : "found";

        console.log("==> Artifact", name, artifactStatus);
        console.log("==> download", download);

        core.setOutput("status", artifactStatus);

        if (artifactStatus === "found" && download == "true") {
            console.log("==> # artifacts:", goodArtifacts.length);

            const artifact = goodArtifacts[0];
            console.log("==> Artifact:", artifact.id)

            const size = filesize(artifact.size, { base: 10 })
            console.log(`==> Downloading: ${artifact.name} (${size}) to path: ${path}`)

            const dir = pathname.dirname(path)
            console.log(`==> Creating containing dir if needed: ${dir}`)
            fs.mkdirSync(dir, { recursive: true })

            await exec.exec('curl', [
                '-L',
                '-o', path,
                '-H', 'Accept: application/octet-stream',
                '-H', `Authorization: token ${token}`,
                artifact.url
            ])
        }

        if (artifactStatus === "missing" && download == "true") {
            core.setFailed("Required", name, "that is missing");
        }

        return;
    } catch (err) {
        console.error(err.stack);
        core.setFailed(err.message);
    }
}

main();
