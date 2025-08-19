import UnityPy
import lz4.block
from tqdm import tqdm
from pathlib import Path
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


def extract_spine_models(file_path):
    asset = UnityPy.load(str(file_path)).assets[0]
    for value in asset.values():
        if value.container and "spineres" in value.container and any(kw in value.container for kw in ["artificial", "corssfaction2", "crossfaction", "cutin", "poster"]):
            if value.type.name in ["TextAsset", "Texture2D"]:
                data = value.read()
                out_dir = Path(value.container.replace("assets/", "")).parent
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = Path(out_dir, data.m_Name)
                if value.type.name == "TextAsset" and value.container.endswith(".txt"):
                    with open(out_path, "w", encoding="utf8") as f:
                        f.write(data.m_Script.replace("\r\n","\n"))
                elif value.type.name == "TextAsset" and value.container.endswith(".bytes"):
                    with open(out_path, "wb") as f:
                        f.write(data.m_Script.encode("utf-8", "surrogateescape"))
                elif value.type.name == "Texture2D":
                    data.image.save(f"{out_path}.png")


if __name__ == "__main__":
    file_list = [p for p in Path("AssetBundles").iterdir() if p.is_file()]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(extract_spine_models, file_path) for file_path in file_list]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Extracting"):
            pass
