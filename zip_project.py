
import os
import zipfile

def zip_project(output_filename='project_backup.zip'):
    exclude_dirs = {'__pycache__', 'venv', '.git', 'instance', 'node_modules', '.idea', '.vscode'}
    exclude_files = {output_filename, 'database.db', 'telemedicine.db'}
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file in exclude_files:
                    continue
                if file.endswith('.pyc') or file.endswith('.pyo') or file.endswith('.pyd'):
                    continue
                    
                file_path = os.path.join(root, file)
                # maintain directory structure relative to current directory
                arcname = os.path.relpath(file_path, '.')
                zipf.write(file_path, arcname)
                
    print(f"Project successfully zipped to {output_filename}")

if __name__ == "__main__":
    zip_project()
