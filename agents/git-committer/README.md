# git-committer

**Track:** Track 3 - Agent Society

## Purpose

Reviews staged diffs and writes conventional commit messages, following shared code conventions from the brain. Demonstrates an agent that both reads shared context and contributes back to it.

## Setup

To use the git-committer agent with DashScope, follow these steps:

1. **Install dependencies**:

   ```
   pip install -r requirements.txt
   ```

2. **Obtain API Key**: Log in to the [DashScope console](https://dashscope.console.aliyun.com/) and navigate to the API Key section to generate or retrieve your API key.

3. **Create .env File**: In the root directory of the project, create a `.env` file if it doesn't already exist.

4. **Set API Key**: Add the following line to the `.env` file, replacing `your_api_key_here` with your actual DashScope API key:
   ```
   DASHSCOPE_API_KEY=your_api_key_here
   ```

## Alibaba Cloud Deployment

To deploy the git-committer agent to Alibaba Cloud infrastructure, follow these steps:

1. **Obtain Alibaba Cloud Credentials**: Log in to the [Alibaba Cloud Console](https://account.aliyun.com/login/login.htm) and navigate to the RAM (Resource Access Management) section to create an AccessKey ID and Secret. Ensure the account has necessary permissions for deploying resources.

2. **Update .env File**: Add the following lines to your `.env` file in the project root:

   ```
   ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key_id
   ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_access_key_secret
   ```

3. **Run Deployment Script**: Execute the deployment command:

   ```
   python deploy.py --region cn-hangzhou --instance-type ecs.g7.large
   ```

   Replace `cn-hangzhou` with your desired region and `ecs.g7.large` with the appropriate instance type.

4. **Verify Deployment**: After deployment, verify the agent is running by checking the instance status in the Alibaba Cloud Console or using SSH to connect to the instance and check the agent logs.

## WebUI Frontend

The git-committer now includes a WebUI for easier interaction. To start the WebUI:

1. Ensure the `.env` file is set up with your DashScope API key (as per Setup section).

2. Run the following command in the project root:

   ```
   python webui.py
   ```

3. Open your browser to `http://localhost:5000` to access the interface.

### Usage

Once the WebUI is running, follow these steps to interact with the agent:

- **View Staged Changes**: The interface displays all staged files with their diffs. Each file's changes are shown in a syntax-highlighted viewer, with additions in green and deletions in red.

- **Review Commit Suggestions**: The agent generates a conventional commit message based on the changes. This message appears in a dedicated text area where you can edit it if needed.

- **Inspect Inline Suggestions**: For specific lines of code, the agent provides inline comments or suggestions. These are displayed as annotations next to the relevant lines in the diff viewer.

- **Commit Changes**: After reviewing the changes and commit message, click the "Commit" button to finalize the commit. The WebUI will confirm the action and refresh the interface to show the updated repository state.

This visual interface streamlines the commit process and helps ensure adherence to project conventions.

## Review Pipeline

The `review.py` script is the core component of the review process. It follows these steps:

1. **Collects Staged Changes**: Uses `git diff` to retrieve the current staged changes.

2. **Loads Code Conventions**: Reads from the `shared.code-conventions` namespace in the brain.

3. **Processes with Qwen Model**: Sends the diff and conventions to the Qwen model:

   ```
   Model: qwen2.5-coder-32b-instruct (QWEN_CODER_MODEL)
   Input: git diff + shared.code-conventions context
   Output: conventional commit message + optional inline review notes
   ```

4. **Applies Changes**: Writes the commit message to the repository and updates the `git-committer.private` namespace with learned preferences.

This pipeline ensures that all commits adhere to the project's coding standards and maintain consistency across the codebase.

## Brain Namespaces

| Namespace | Access | Contents |
|---|---|---|
| `shared.code-conventions` | read | Language and style rules shared across agents |
| `git-committer.private` | read/write | Per-repo commit history and learned preferences |
