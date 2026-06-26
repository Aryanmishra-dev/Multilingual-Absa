import os
from huggingface_hub import HfApi

def main():
    api = HfApi()
    repo_name = "multilingual-absa"
    username = os.environ.get("HF_USERNAME", "YOUR_HF_USERNAME")
    repo_id = f"{username}/{repo_name}"

    print(f"Creating repo {repo_id}...")
    try:
        api.create_repo(repo_id, repo_type="model", exist_ok=True)
    except Exception as e:
        print(f"Failed to create repo: {e}")
        return

    print("Uploading models/onnx/ folder...")
    api.upload_folder(
        folder_path="models/onnx/",
        repo_id=repo_id,
        commit_message="Upload INT8 ONNX models for Multilingual ABSA"
    )
    print("Upload complete!")

if __name__ == "__main__":
    main()
