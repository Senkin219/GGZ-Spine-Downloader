import os
import json
import requests
import lz4.block
import UnityPy
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


def decompress_lz4(data, uncompressed_size):
    try:
        decryptor = Cipher(algorithms.AES(b"LPC@a*&^b19b61l/"), modes.CBC(bytes(16))).decryptor()
        unpadder = padding.PKCS7(128).unpadder()
        decrypted_data = unpadder.update(decryptor.update(data) + decryptor.finalize()) + unpadder.finalize()
        return lz4.block.decompress(decrypted_data, uncompressed_size)
    except Exception:
        return lz4.block.decompress(data, uncompressed_size)


UnityPy.helpers.CompressionHelper.DECOMPRESSION_MAP[3] = decompress_lz4


def download_file(url, dest_path, max_retries=3):
    for attempt in range(max_retries):
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            return
        except Exception:
            if attempt == max_retries - 1:
                raise


def get_existing_files(directory="AssetBundles"):
    files = {}
    for f in os.listdir(directory):
        if "_" in f:
            name, crc = f.rsplit("_", 1)
            files[name] = (f, crc)
    return files


def download_single_asset(info, existing_files, game_version):
    filename, crc, filesize = info["N"], info["CRC"], int(info["FS"])
    existing = existing_files.get(filename)
    if existing and existing[1] == crc and os.path.getsize(os.path.join("AssetBundles", existing[0])) == filesize:
        return
    if existing:
        os.remove(os.path.join("AssetBundles", existing[0]))
    local_path = os.path.join("AssetBundles", f"{filename}_{crc}")
    url = f"https://assets-ios.hsod2.benghuai.com/asset_bundle/{game_version}/original/iphone/Res/AssetBundles/{filename}_{crc}"
    try:
        download_file(url, local_path)
    except Exception as e:
        print(f"Download failed: {filename} {e}")


def add_with_pn(n, download_set, info_dict):
    if n in download_set:
        return
    download_set.add(n)
    for pn in info_dict.get(n, {}).get("PN", "").split(";"):
        if pn:
            add_with_pn(pn, download_set, info_dict)


def download_game_assets(manifest, game_version, max_workers=6):
    infos = [json.loads(line) for line in manifest.splitlines()[2:] if "StreamingAssets" not in line]
    info_dict = {info["N"]: info for info in infos}
    download_set = set()
    for info in infos:
        aps = info.get("APS", [])
        if any("MenusV2/Partner/AllPartnerMiscShow" in a or "MenusV2/CutIn" in a for a in aps):
            add_with_pn(info["N"], download_set, info_dict)
    existing_files = get_existing_files("AssetBundles")
    for existing_file in existing_files:
        if existing_file not in download_set:
            os.remove(os.path.join("AssetBundles", existing_files[existing_file][0]))
    download_infos = [info for info in infos if info["N"] in download_set]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_single_asset, info, existing_files, game_version) for info in download_infos]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Downloading"):
            pass


def get_version():
    version = requests.get("https://apps.apple.com/cn/app/id737651307?dataOnly=true").json()["pageData"]["versionHistory"][0]["versionString"].split(".")
    return f"{version[0]}_{version[1]}"


if __name__ == "__main__":
    game_version = get_version()
    os.makedirs("AssetBundles", exist_ok=True)
    download_file(f"https://assets-ios.hsod2.benghuai.com/asset_bundle/{game_version}/original/iphone/Data/ResourceVersion.unity3d", "AssetBundles/ResourceVersion.unity3d")
    asset = UnityPy.load("AssetBundles/ResourceVersion.unity3d").assets[0]
    manifest = next((v.read().m_Script for v in asset.values() if v.type.name == "TextAsset"), None)
    if manifest:
        download_game_assets(manifest, game_version)
