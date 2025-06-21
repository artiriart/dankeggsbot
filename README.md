## Dank Memer minimal Eggs Events Bot/s

###### Minimal ressource hungry discord.py script

---

### How to setup:

#### Linux:

1. Clone this repo

```bash
git clone https://github.com/artiriart/dankeggsbot.git
```

2. Install required pip Packages

```bash
# cd /dankeggsbot
pip install -r requirements.txt # Packages used: discord,discord.py
```

3. Create a file named "tokens.json" which consists of a List of Tokens

```bash
echo [] > tokens.json
```

4. Adjust the Variables inside config.json
```bash
nano config.json # a few lines need editing (inserting ID's)
```

5. Run the Bot/s

```bash
python3 index.py
```

#### Windows:

Sure! Here's the **same setup but formatted for Windows**, using your original Markdown style:

---

1. Clone this repo

```bash
git clone https://github.com/artiriart/dankeggsbot.git
cd dankeggsbot
```

2. Install required pip Packages

```bash
pip install -r requirements.txt
```

3. Create a file named "tokens.json" which consists of a List of Tokens

```bash
echo [] > tokens.json
```

4. Adjust the Variables inside config.json

```bash
notepad config.json
# insert your guild/channel/role IDs
```

5. Run the Bot/s

```bash
python index.py
# or if python doesn't work:
# py index.py
```