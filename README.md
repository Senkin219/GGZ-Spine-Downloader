# GGZ-Spine-Downloader

Scripts to download and extract Spine models from Houkai Gakuen 2 (Guns Girl Z).

## Usage

1. **Install Dependencies**

   Install the required libraries manually using pip:

   ```bash
   pip install UnityPy==1.22.2 requests tqdm cryptography
   ```

2. **Download Game Assets**

   Run the following script to download the game asset bundles. The files will be saved in the `AssetBundles` directory:

   ```bash
   python download_game_assets.py
   ```

3. **Extract Spine Models**

   After the assets are downloaded, extract the Spine models by running:

   ```bash
   python extract_spine_models.py
   ```

   The extracted models will be saved in the `spineres` directory.