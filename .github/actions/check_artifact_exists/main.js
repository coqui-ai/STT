const core = require('@actions/core');
const github = require('@actions/github');
const AdmZip = require('adm-zip');
const filesize = require('filesize');
const pathname = require('path');
const fs = require('fs');

async function getGoodArtifacts(client, owner, repo, name) {
    const goodWorkflowArtifacts = await client.paginate(
        "GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts",
        {
            owner: owner,
            repo: repo,
            run_id: github.context.runId,
        },
        (workflowArtifacts) => {
            // console.log(" ==> workflowArtifacts", workflowArtifacts);
            return workflowArtifacts.data.filter((a) => {
                // console.log("==> Artifact check", a);
                return a.name == name
            })
        }
    );

    console.log("==> maybe goodWorkflowArtifacts:", goodWorkflowArtifacts);
    if (goodWorkflowArtifacts.length > 0) {
        return goodWorkflowArtifacts;
    }

    const goodRepoArtifacts = await client.paginate(
        "GET /repos/{owner}/{repo}/actions/artifacts",
        {
            owner: owner,
            repo: repo,
        },
        (repoArtifacts) => {
            // console.log(" ==> repoArtifacts", repoArtifacts);
            return repoArtifacts.data.filter((a) => {
                // console.log("==> Artifact check", a);
                return a.name == name
            })
        }
    );

    console.log("==> maybe goodRepoArtifacts:", goodRepoArtifacts);
    if (goodRepoArtifacts.length > 0) {
        return goodRepoArtifacts;
    }

    // We have not been able to find a repo artifact, it's really no good news
    return [];
}

async function main() {
    const token = core.getInput("github_token", { required: true });
    const [owner, repo] = core.getInput("repo", { required: true }).split("/");
    const path = core.getInput("path", { required: true });
    const name = core.getInput("name");
    const download = core.getInput("download");
    const client = github.getOctokit(token)

    console.log("==> Repo:", owner + "/" + repo);

    const goodArtifacts = await getGoodArtifacts(client, owner, repo, name);
    console.log("==> goodArtifacts:", goodArtifacts);

    let artifactStatus = "";
        if (goodArtifacts.length === 0) {
        artifactStatus = "missing";
    } else {
        artifactStatus = "found";
    }

    console.log("==> Artifact", name, artifactStatus);
    console.log("==> download", download);

    core.setOutput("status", artifactStatus);

    if (artifactStatus === "found" && download == "true") {
        console.log("==> # artifacts:", goodArtifacts.length);

        let artifact = goodArtifacts[0];

        console.log("==> Artifact:", artifact.id)

        const size = filesize(artifact.size_in_bytes, { base: 10 })

        console.log("==> Downloading:", artifact.name + ".zip", `(${size})`)

        const zip = await client.actions.downloadArtifact({
            owner: owner,
            repo: repo,
            artifact_id: artifact.id,
            archive_format: "zip",
        })

        const dir = name ? path : pathname.join(path, artifact.name)

        fs.mkdirSync(dir, { recursive: true })

        const adm = new AdmZip(Buffer.from(zip.data))

        adm.getEntries().forEach((entry) => {
            const action = entry.isDirectory ? "creating" : "inflating"
            const filepath = pathname.join(dir, entry.entryName)
            console.log(`  ${action}: ${filepath}`)
        })

        adm.extractAllTo(dir, true)
    }

    if (artifactStatus === "missing" && download == "true") {
        core.setFailed("Required", name, "that is missing");
    }

    return;
}

main();
