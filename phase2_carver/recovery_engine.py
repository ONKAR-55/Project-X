import os
import shutil

class BatchRecoveryEngine:
    """Handles batch extraction and structured cataloging of carved artifacts."""

    def recover_artifacts(self, artifacts: list, destination_dir: str) -> dict:
        os.makedirs(destination_dir, exist_ok=True)

        total_recovered = 0
        total_bytes = 0

        for idx, artifact in enumerate(artifacts, start=1):
            category = artifact.get("category", "Unclassified")
            cat_dir = os.path.join(destination_dir, category)
            os.makedirs(cat_dir, exist_ok=True)

            # Use original filename if available; fallback to signature naming for raw carves
            original_name = artifact.get("original_name")
            if original_name:
                filename = original_name
            else:
                file_ext = artifact.get("type", "bin").lower()
                sha_prefix = artifact.get("sha256", "")[:8] or f"item_{idx}"
                filename = f"carved_{idx:03d}_{sha_prefix}.{file_ext}"

            # Prevent overwriting if multiple files share the exact same original name
            dest_path = os.path.join(cat_dir, filename)
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(dest_path):
                dest_path = os.path.join(cat_dir, f"{base_name}_{counter}{ext}")
                counter += 1

            source_path = artifact.get("source_file")

            try:
                if source_path and os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                else:
                    # Fallback for raw disk sector carving
                    offset = artifact.get("offset", 0)
                    size = artifact.get("size_bytes", 0)
                    target_media = artifact.get("drive_path") or source_path

                    if target_media and os.path.exists(target_media):
                        with open(target_media, "rb") as f_in:
                            f_in.seek(offset)
                            raw_bytes = f_in.read(size)
                        with open(dest_path, "wb") as f_out:
                            f_out.write(raw_bytes)

                total_recovered += 1
                total_bytes += artifact.get("size_bytes", 0)

            except Exception as err:
                print(f"[!] Error restoring artifact #{idx} ({filename}): {err}")

        return {
            "total_recovered": total_recovered,
            "total_bytes": total_bytes
        }