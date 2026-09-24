#!/usr/bin/env python3
"""Expand Part 0 into full #equipment + searchable #ingredients encyclopedia for both cookbooks."""
from __future__ import annotations
import json, re, html
from pathlib import Path
from collections import defaultdict, Counter
from html.parser import HTMLParser

ROOTS = {
    "southern": Path("/workspace/chef_cookbook"),
    "chinese": Path("/workspace/chinese_cookbook"),
}

SOUTHERN_EQUIP = [
    ("kit-cast-iron.png", "Cast-Iron Skillet", "Fried chicken, cornbread, blackened fish, skillet cobbler — the Southern multitool. Season it; don't soak it."),
    ("kit-dutch-oven.png", "Dutch Oven", "Gumbo, beans, short ribs, peach cobbler under a biscuit lid. Heavy lid traps patience."),
    ("kit-fry-pot.png", "Deep-Fry Pot", "Tall sides, steady heat. Pair with a clip-on thermometer for shatter-crisp crust."),
    ("kit-thermometer.png", "Fry / Instant-Read Thermometer", "350°F gospel for frying; probe meats so juiciness isn't a guess."),
    ("kit-biscuit-tools.png", "Biscuit Cutter & Bench Tools", "Sharp cutter, cold hands, light touch. Never twist the cutter."),
    ("kit-sheet-pan.png", "Sheet Pan", "Roasted nuts, sheet-pan supper, toasting pecans for pie."),
    ("kit-mixing-bowls.png", "Mixing Bowls", "Buttermilk dredge, wet/dry stations, and the great Southern mise en place."),
    ("kit-wire-rack.png", "Wire Cooling Rack", "Fried chicken rests here so steam doesn't sog the crust."),
    ("kit-stockpot.png", "Stockpot", "Greens, stocks, and big-batch gumbo when the Dutch oven runs out of room."),
    ("kit-pie-plate.png", "Ceramic Pie Plate", "Pecan, sweet potato, chess — glass or ceramic browns the bottom clean."),
]

SOUTHERN_FEATURED = [
    ("pantry-buttermilk.png", "Buttermilk", "Tang for biscuits, soak for chicken, lift for cornbread."),
    ("pantry-cornmeal.png", "Cornmeal", "Self-rising or plain — the yellow backbone of the South."),
    ("pantry-hot-sauce.png", "Hot Sauce", "Vinegar heat that finishes greens, eggs, and fried fish."),
    ("pantry-smoked-meat.png", "Smoked Meat", "Turkey necks, ham hocks, bacon — the quiet seasoning of pots."),
    ("pantry-molasses.png", "Molasses / Sorghum", "Deep sweetness for beans, gingerbread, and barbecue glaze."),
    ("pantry-pecans.png", "Pecans", "Pie, pralines, toasted garnish — Southern gold."),
]

CHINESE_EQUIP = [
    ("kit-wok.png", "Carbon-Steel Wok", "High heat, fast toss, wok hei when the burner allows. Season like cast iron."),
    ("kit-wok-flame.png", "Wok over Flame", "The drama shot: oil shimmer, aromatics bloom, steam shooting up."),
    ("kit-cleaver.png", "Chinese Cleaver", "Chop, smash garlic, scoop — one blade, many jobs."),
    ("kit-bamboo-steamer.png", "Bamboo Steamer", "Bao, dumplings, fish — gentle steam in stacked trays."),
    ("kit-steamer-tower.png", "Steamer Tower", "Stack trays for a dim-sum parade without crowding."),
    ("kit-spider.png", "Spider Strainer", "Lift noodles, skim fry oil, scoop blanched greens."),
    ("kit-spider-lift.png", "Spider Lift", "Noodles rising from the boil — lunch in one swoop."),
    ("kit-rice-cooker.png", "Rice Cooker", "Perfect jasmine on autopilot while the wok works."),
]

CHINESE_FEATURED = [
    ("pantry-soy.png", "Soy Sauce", "Light for seasoning, dark for color — the pantry's salt and soul."),
    ("pantry-oyster.png", "Oyster Sauce", "Glossy umami for beef & broccoli and weeknight stir-fries."),
    ("pantry-sesame-oil.png", "Toasted Sesame Oil", "Finish, don't fry — a few drops announce dinner."),
    ("pantry-cornstarch.png", "Cornstarch", "Velvet meats, gloss sauces, crisp coatings."),
    ("pantry-shaoxing.png", "Shaoxing Wine", "Marinades and deglazes — the kitchen's red wine."),
    ("pantry-trinity.png", "Ginger · Garlic · Scallion", "The wok trinity. Bloom in hot oil and the kitchen wakes up."),
]

# Curated Chinese/American-Chinese pantry (Western-friendly)
CHINESE_CURATED = [
    ("Soy sauce (light)", "Sauces & Condiments", "Everyday seasoning salt of the Chinese kitchen."),
    ("Dark soy sauce", "Sauces & Condiments", "Color and molasses depth for braises and fried rice."),
    ("Oyster sauce", "Sauces & Condiments", "Glossy savory backbone of takeout brown sauce."),
    ("Hoisin sauce", "Sauces & Condiments", "Sweet-salty glaze for ribs, mu shu, and bao."),
    ("Toasted sesame oil", "Oils & Fats", "Aromatic finish oil — never the fry medium."),
    ("Neutral oil", "Oils & Fats", "Peanut, canola, or vegetable for high-heat wok work."),
    ("Shaoxing wine", "Sauces & Condiments", "Cooking wine for marinades and deglazing."),
    ("Rice vinegar", "Sauces & Condiments", "Bright acid for sweet-and-sour and dumpling dips."),
    ("Black vinegar", "Sauces & Condiments", "Smoky tang for dumplings and Shanghainese notes."),
    ("Doubanjiang", "Sauces & Condiments", "Fermented chile-bean paste — mapo and twice-cooked soul."),
    ("Chili crisp / chili oil", "Sauces & Condiments", "Crunchy heat you spoon on everything."),
    ("Fermented black beans", "Sauces & Condiments", "Salty depth for black-bean ribs and clams."),
    ("Ketchup", "Sauces & Condiments", "American-Chinese sweet-and-sour secret."),
    ("Cornstarch", "Starches & Grains", "Velvet, thicken, and crisp."),
    ("All-purpose flour", "Starches & Grains", "Batter for orange chicken and egg foo young."),
    ("Potato starch", "Starches & Grains", "Extra-crisp fry coating when you want shatter."),
    ("Jasmine rice", "Starches & Grains", "Daily steamer rice; fry only when day-old and cold."),
    ("Egg noodles", "Starches & Grains", "Lo mein and chow mein workhorse."),
    ("Rice noodles", "Starches & Grains", "Pad-adjacent stir-fries and soups."),
    ("Wonton wrappers", "Starches & Grains", "Wontons, rangoon, and emergency dumpling skins."),
    ("Egg roll wrappers", "Starches & Grains", "Crispy rolls and leftover-night heroes."),
    ("Spring roll wrappers", "Starches & Grains", "Thinner sheet for lighter crunch."),
    ("Tofu (firm)", "Proteins", "Mapo, hot pot add-in, pan-sear for texture."),
    ("Tofu (soft/silken)", "Proteins", "Gentle soups and steamed dishes."),
    ("Chicken thighs", "Proteins", "Dark meat stays juicy through fry and velvet."),
    ("Chicken breast", "Proteins", "Velvet thin for white-sauce classics."),
    ("Pork belly", "Proteins", "Red-braise (hong shao) glory."),
    ("Ground pork", "Proteins", "Dumplings, mapo, egg foo young."),
    ("Pork shoulder", "Proteins", "Char siu and pulled fillings."),
    ("Beef flank", "Proteins", "Velvet against the grain for stir-fry."),
    ("Shrimp", "Proteins", "Quick-cook star of fried rice and lo mein."),
    ("Eggs", "Proteins", "Fried rice, egg drop, tomato-egg comfort."),
    ("Imitation crab", "Proteins", "Rangoon filling classic."),
    ("Cream cheese", "Dairy", "Rangoon richness (American-Chinese)."),
    ("Ginger", "Aromatics & Produce", "Smashed, minced, or julienned — never optional."),
    ("Garlic", "Aromatics & Produce", "Bloom in oil before anything else hits the wok."),
    ("Scallions", "Aromatics & Produce", "White for cooking, green for finish."),
    ("Yellow onion", "Aromatics & Produce", "Pepper steak and fajita-adjacent stir-fries."),
    ("Shallot", "Aromatics & Produce", "Sweeter aromatic for finer sauces."),
    ("Napa cabbage", "Aromatics & Produce", "Dumpling filling and gentle stir-fries."),
    ("Bok choy", "Aromatics & Produce", "Quick garlic greens."),
    ("Broccoli", "Aromatics & Produce", "Beef & broccoli canon."),
    ("Bell pepper", "Aromatics & Produce", "Sweet-and-sour color and crunch."),
    ("Snow peas", "Aromatics & Produce", "Bright snap in white-sauce dishes."),
    ("Carrot", "Aromatics & Produce", "Fried rice dice and dumpling mix."),
    ("Celery", "Aromatics & Produce", "Chop suey crunch."),
    ("Mushroom (button/shiitake)", "Aromatics & Produce", "Moo goo and braises."),
    ("Bean sprouts", "Aromatics & Produce", "Last-second crunch for chow mein."),
    ("Water chestnuts", "Aromatics & Produce", "Canned crunch that survives the steam table."),
    ("Bamboo shoots", "Aromatics & Produce", "Classic stir-fry extender."),
    ("Baby corn", "Aromatics & Produce", "Buffet nostalgia, legitimately fun."),
    ("Tomato", "Aromatics & Produce", "Tomato-egg and sweet-sour brightness."),
    ("Cucumber", "Aromatics & Produce", "Cool contrast for spicy plates."),
    ("Pineapple", "Aromatics & Produce", "Sweet-and-sour fruit punch."),
    ("Orange zest / juice", "Aromatics & Produce", "Orange chicken perfume."),
    ("Lemon", "Aromatics & Produce", "Lemon chicken glaze."),
    ("Peanuts", "Nuts & Seeds", "Kung pao crunch."),
    ("Cashews", "Nuts & Seeds", "Cashew chicken glory."),
    ("Almonds", "Nuts & Seeds", "Almond boneless finish."),
    ("Sesame seeds", "Nuts & Seeds", "Toast and scatter."),
    ("White pepper", "Spices", "Egg drop and hot-and-sour whisper heat."),
    ("Black pepper", "Spices", "Universal finish."),
    ("Five-spice powder", "Spices", "Char siu and roast pork perfume."),
    ("Star anise", "Spices", "Red-braise bouquet."),
    ("Sichuan peppercorn", "Spices", "Mala tingle — use with a light hand."),
    ("Dried red chiles", "Spices", "Kung pao and dry-fried heat."),
    ("Bay leaf", "Spices", "Occasional braise cameo."),
    ("Sugar", "Pantry Staples", "Balances soy and vinegar."),
    ("Brown sugar", "Pantry Staples", "Char siu and Mongolian sweetness."),
    ("Honey", "Pantry Staples", "Sticky glaze shine."),
    ("Salt", "Pantry Staples", "Still needed even with soy."),
    ("Baking soda", "Pantry Staples", "Velveting helper for meat."),
    ("Chicken stock", "Pantry Staples", "Soups, sauces, and egg drop body."),
    ("MSG (optional)", "Pantry Staples", "Restaurant savor; a pinch is plenty."),
    ("Food coloring (optional)", "Pantry Staples", "Buffet-red char siu look — skip if you prefer natural."),
    ("Light soy sauce", "Sauces & Condiments", "Salt-forward seasoning for marinades and finishing."),
    ("Seasoned soy sauce", "Sauces & Condiments", "Table dip for dumplings when mixed with vinegar."),
    ("Sweet bean sauce", "Sauces & Condiments", "Jingjiang-style noodles and Peking duck pancakes."),
    ("Bean paste (tianmianjiang)", "Sauces & Condiments", "Sweet wheat paste for northern noodles."),
    ("Chinkiang vinegar", "Sauces & Condiments", "Another name for black vinegar — dumpling essential."),
    ("Mirin (or rice wine mild)", "Sauces & Condiments", "Optional mild sweetness if Shaoxing is too strong."),
    ("Fish sauce (dash)", "Sauces & Condiments", "Occasional umami boost in modern fusion plates."),
    ("XO sauce", "Sauces & Condiments", "Luxury seafood chile jam for fried rice upgrades."),
    ("Sriracha", "Sauces & Condiments", "American fridge heat for takeout nights."),
    ("Duck sauce", "Sauces & Condiments", "Packet-orange sweet dip for egg rolls."),
    ("Plum sauce", "Sauces & Condiments", "Fruity glaze for roast duck and rolls."),
    ("Garlic chili sauce", "Sauces & Condiments", "Sambal-adjacent heat for noodles."),
    ("Sesame paste (zhima jiang)", "Sauces & Condiments", "Northern cold noodles and hot pot dip."),
    ("Peanut butter", "Sauces & Condiments", "Emergency sesame-paste stand-in for cold noodles."),
    ("Lard", "Oils & Fats", "Old-school fried rice perfume."),
    ("Chicken fat", "Oils & Fats", "Schmaltz for ginger-scallion oil."),
    ("Chile oil sediment", "Oils & Fats", "The crunchy bits at the bottom of the jar."),
    ("Short-grain rice", "Starches & Grains", "Stickier bowls and sushi-adjacent sides."),
    ("Brown rice", "Starches & Grains", "Health-menu swap; cook longer."),
    ("Glutinous rice", "Starches & Grains", "Sticky rice for zongzi and sweet fillings."),
    ("Rice flour", "Starches & Grains", "Cheung fun and some batters."),
    ("Wheat starch", "Starches & Grains", "Crystal dumpling wrappers."),
    ("Tapioca starch", "Starches & Grains", "Q-chewy bounce in sauces and boba-adjacent."),
    ("Panko", "Starches & Grains", "Extra crunch for fusion cutlets."),
    ("Lo mein noodles", "Starches & Grains", "Fresh wheat noodles that drink sauce."),
    ("Chow mein noodles", "Starches & Grains", "Crispy or soft — know your regional quarrel."),
    ("Udon / thick wheat noodles", "Starches & Grains", "Hearty bowls when egg noodles run out."),
    ("Rice vermicelli", "Starches & Grains", "Mei fun and soup add-ins."),
    ("Glass noodles", "Starches & Grains", "Ants-climbing-tree and hot pot."),
    ("Dumpling wrappers", "Starches & Grains", "Round skins for potstickers and boiled jiaozi."),
    ("Hong Kong-style wonton noodles", "Starches & Grains", "Alkaline bounce for soup wontons."),
    ("Dried shiitake", "Aromatics & Produce", "Soak, save the liquor, braise deep."),
    ("Wood ear mushrooms", "Aromatics & Produce", "Crunchy fungus for hot-and-sour."),
    ("Enoki mushrooms", "Aromatics & Produce", "Hot pot and quick garlic sautés."),
    ("Chinese broccoli (gai lan)", "Aromatics & Produce", "Oyster-sauce greens classic."),
    ("Chinese eggplant", "Aromatics & Produce", "Fish-fragrant and garlic sauces."),
    ("Long beans", "Aromatics & Produce", "Dry-fried with pork."),
    ("Yardlong beans", "Aromatics & Produce", "Same family — wok blister them."),
    ("Lotus root", "Aromatics & Produce", "Crunchy slices for stir-fry and soup."),
    ("Daikon radish", "Aromatics & Produce", "Soups and gentle braises."),
    ("Chinese mustard greens", "Aromatics & Produce", "Pickled or stir-fried bitter-green (mild)."),
    ("Spinach", "Aromatics & Produce", "Garlic wilt side."),
    ("Romaine / iceberg", "Aromatics & Produce", "Chop suey and lettuce wraps."),
    ("Zucchini", "Aromatics & Produce", "Mild stir-fry extender."),
    ("Green beans", "Aromatics & Produce", "Dry-fried Sichuan style."),
    ("Asparagus", "Aromatics & Produce", "Quick velvet-chicken partner."),
    ("Corn kernels", "Aromatics & Produce", "Egg-drop corn soup."),
    ("Peas", "Aromatics & Produce", "Fried rice green pearls."),
    ("Edamame", "Aromatics & Produce", "Appetizer bowl with salt."),
    ("Silken tofu pudding mix", "Proteins", "Optional dessert night."),
    ("Pressed tofu", "Proteins", "Slices for cold appetizers."),
    ("Fried tofu puffs", "Proteins", "Soak up braising liquid."),
    ("Duck", "Proteins", "Roast duck or leftover fried rice luxury."),
    ("Whole fish (bass/tilapia)", "Proteins", "Steamed fish with ginger-scallion oil."),
    ("Scallops", "Proteins", "Velvet with asparagus."),
    ("Squid", "Proteins", "Salt-and-pepper or stir-fry."),
    ("Pork ribs", "Proteins", "Sweet-sour or black-bean steam."),
    ("Spare ribs", "Proteins", "Char siu sticky glaze."),
    ("Ground chicken", "Proteins", "Lighter dumpling filling."),
    ("Ground beef", "Proteins", "American-Chinese meat sauce nights."),
    ("Bacon", "Proteins", "Fried rice smoke (untraditional, delicious)."),
    ("Ham", "Proteins", "Yangzhou fried rice cubes."),
    ("Char siu (store-bought)", "Proteins", "Shortcut roast pork for fried rice."),
    ("Lap cheong", "Proteins", "Sweet Chinese sausage for clay pot rice."),
    ("Cilantro", "Aromatics & Produce", "Love-it-or-leave-it finish."),
    ("Thai basil", "Aromatics & Produce", "Occasional fusion finish."),
    ("Lime", "Aromatics & Produce", "Bright squeeze for seafood."),
    ("Orange segments", "Aromatics & Produce", "Orange beef garnish."),
    ("Chestnuts", "Nuts & Seeds", "Braised chicken winter plate."),
    ("Walnuts", "Nuts & Seeds", "Honey walnut shrimp."),
    ("Pine nuts", "Nuts & Seeds", "Occasional garnish luxury."),
    ("Cumin", "Spices", "Xi'an-style lamb vibes."),
    ("Fennel seed", "Spices", "Braise bouquet."),
    ("Coriander seed", "Spices", "Warm braise spice."),
    ("Cloves", "Spices", "Red-braise tiny dots."),
    ("Cinnamon stick", "Spices", "Master stock perfume."),
    ("Dried tangerine peel", "Spices", "Chenpi aroma for braises."),
    ("White sesame oil (untoasted)", "Oils & Fats", "Neutral sesame for frying if needed."),
    ("Rock sugar", "Pantry Staples", "Hong shao shine."),
    ("Maltose", "Pantry Staples", "Peking duck skin lacquer."),
    ("Shaoxing substitute dry sherry", "Sauces & Condiments", "Pantry backup when Shaoxing is scarce."),
    ("Chicken bouillon powder", "Pantry Staples", "Weeknight stock shortcut."),
    ("Vegetable stock", "Pantry Staples", "Meatless mapo and greens."),
    ("Cornstarch slurry", "Pantry Staples", "Equal parts starch + cold water — sauce gloss."),
    ("Egg whites", "Proteins", "Velveting and egg foo young lift."),
    ("Sha cha sauce", "Sauces & Condiments", "BBQ-ish umami for beef hot pot."),
    ("Curry powder (HK style)", "Spices", "British-Hong Kong curry beef."),
    ("Turmeric", "Spices", "Curry color."),
    ("Coconut milk", "Dairy", "Southeast-leaning curry bowls."),
    ("Mayonnaise", "Dairy", "Honey walnut shrimp sauce."),
    ("Sweetened condensed milk", "Dairy", "Mango pudding / toast dessert."),
    ("Agar / gelatin", "Pantry Staples", "Mango pudding set."),
    ("Wonton soup base", "Pantry Staples", "Light chicken broth + sesame oil + white pepper."),
    ("Pickled mustard greens", "Aromatics & Produce", "Sour crunch for noodles."),
    ("Preserved radish", "Aromatics & Produce", "Fried rice salty pops."),
    ("Kimchi (fusion)", "Aromatics & Produce", "Modern fried rice heat."),
    ("Goji berries", "Pantry Staples", "Soup garnish, mild sweet."),
    ("Dried red dates", "Pantry Staples", "Gentle soup sweetness."),
    ("Soy milk", "Dairy", "Breakfast and cooking mild base."),

]

UNIT_PREFIX = re.compile(
    r"^(?:"
    r"[\d¼½¾⅓⅔⅛⅜⅝⅞]+(?:\s*/\s*[\d¼½¾⅓⅔⅛⅜⅝]+)?|"
    r"\d+\s*[-–]\s*\d+|"
    r"\d+\s*\d/\d+"
    r")\s*",
    re.I,
)
UNIT_WORDS = re.compile(
    r"^(?:"
    r"cups?|cup|tbsps?|tbsp|tablespoons?|tsps?|tsp|teaspoons?|"
    r"oz|ounces?|lbs?|pounds?|g|grams?|kg|ml|l|"
    r"cloves?|pinch(?:es)?|dashes?|cans?|packages?|packs?|bunches?|"
    r"slices?|sticks?|heads?|ears?|ribs?|links?|bags?|boxes?|"
    r"quarts?|pints?|gallons?|inches?|large|medium|small|whole|"
    r"sticks?|sprigs?|leaves?"
    r")\b\.?\s*",
    re.I,
)
PREP_SUFFIX = re.compile(
    r",?\s*(?:diced|minced|chopped|sliced|cubed|crumbled|melted|softened|"
    r"room[- ]temp(?:erature)?|beaten|divided|to taste|optional|plus more.*|"
    r"peeled|deveined|drained|rinsed|thawed|cut into.*|as needed).*$",
    re.I,
)

CANON_MERGE = {
    "melted butter": "butter",
    "unsalted butter": "butter",
    "salted butter": "butter",
    "butter, melted": "butter",
    "egg": "eggs",
    "large eggs": "eggs",
    "large egg": "eggs",
    "garlic clove": "garlic",
    "garlic cloves": "garlic",
    "clove garlic": "garlic",
    "cloves garlic": "garlic",
    "yellow onion": "onion",
    "white onion": "onion",
    "onions": "onion",
    "green onion": "scallions",
    "green onions": "scallions",
    "scallion": "scallions",
    "kosher salt": "salt",
    "sea salt": "salt",
    "table salt": "salt",
    "black pepper": "black pepper",
    "freshly ground black pepper": "black pepper",
    "ground black pepper": "black pepper",
    "all purpose flour": "all-purpose flour",
    "ap flour": "all-purpose flour",
    "vegetable oil": "neutral oil",
    "canola oil": "neutral oil",
    "peanut oil": "neutral oil",
    "cooking oil": "neutral oil",
}

CAT_RULES = [
    (("butter", "buttermilk", "milk", "cream", "cheese", "egg", "sour cream", "half-and-half", "cheddar", "parmesan"), "Dairy & Eggs"),
    (("chicken", "turkey", "pork", "beef", "ham", "bacon", "sausage", "shrimp", "crab", "fish", "oyster", "catfish", "andouille", "brisket", "ribs"), "Proteins & Seafood"),
    (("flour", "cornmeal", "grits", "rice", "sugar", "brown sugar", "powdered sugar", "baking", "yeast", "cornstarch", "biscuit", "self-rising"), "Flours, Grains & Starches"),
    (("oil", "lard", "shortening", "bacon drippings", "fat", "stock", "broth", "water", "wine", "beer", "vinegar"), "Oils, Fats & Liquids"),
    (("salt", "pepper", "cayenne", "paprika", "thyme", "oregano", "bay", "creole", "cajun", "hot sauce", "mustard", "vanilla", "cinnamon", "nutmeg", "garlic powder", "onion powder", "seasoning"), "Spices, Seasonings & Condiments"),
    (("onion", "garlic", "celery", "pepper", "tomato", "okra", "greens", "collard", "cabbage", "potato", "sweet potato", "corn", "lemon", "lime", "apple", "peach", "berry", "scallion", "parsley", "cilantro", "ginger"), "Produce"),
    (("pecan", "walnut", "peanut", "almond", "molasses", "sorghum", "honey", "maple", "chocolate", "cocoa"), "Pantry Staples & Other"),
]


def categorize(name: str) -> str:
    n = name.lower()
    for keys, cat in CAT_RULES:
        if any(k in n for k in keys):
            return cat
    return "Pantry Staples & Other"


def clean_ingredient(raw: str) -> str | None:
    s = re.sub(r"\s+", " ", raw).strip()
    s = s.strip(" .;:")
    if not s or len(s) < 2:
        return None
    # drop obvious template junk
    low = s.lower()
    if any(x in low for x in ["main protein", "as fits", "mixed veg", "optional skip", "century egg", "steamed rice or noodles, for serving"]):
        return None
    s = UNIT_PREFIX.sub("", s)
    # peel repeated unit words
    for _ in range(4):
        ns = UNIT_WORDS.sub("", s)
        if ns == s:
            break
        s = ns
    s = PREP_SUFFIX.sub("", s).strip(" ,.-")
    s = re.sub(r"\s+", " ", s).strip()
    if not s or len(s) < 2:
        return None
    # fix leading crumbs from bad parses
    if s[0].islower() and len(s) > 3:
        # likely unit ate first letter previously in other parsers — capitalize carefully
        pass
    key = s.lower()
    key = CANON_MERGE.get(key, key)
    # title-ish
    nice = key
    # restore some acronyms
    nice = re.sub(r"\bmsg\b", "MSG", nice, flags=re.I)
    nice = nice[:1].upper() + nice[1:] if nice else nice
    return nice


class RecipeIngParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_recipe = False
        self.recipe_id = None
        self.recipe_title = None
        self.in_ings = False
        self.in_li = False
        self.in_h2 = False
        self.li_buf: list[str] = []
        self.h2_buf: list[str] = []
        self.current_ings: list[str] = []
        self.recipes: list[dict] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class") or ""
        if tag == "article" and "recipe" in cls.split():
            self.in_recipe = True
            self.recipe_id = a.get("id")
            self.current_ings = []
            self.recipe_title = None
        if self.in_recipe and tag == "h2":
            self.in_h2 = True
            self.h2_buf = []
        if self.in_recipe and tag == "ul" and "ings" in cls.split():
            self.in_ings = True
        if self.in_ings and tag == "li":
            self.in_li = True
            self.li_buf = []

    def handle_endtag(self, tag):
        if tag == "h2" and self.in_h2:
            self.in_h2 = False
            self.recipe_title = re.sub(r"\s+", " ", "".join(self.h2_buf)).strip()
        if tag == "li" and self.in_li:
            self.in_li = False
            text = re.sub(r"\s+", " ", "".join(self.li_buf)).strip()
            if text:
                self.current_ings.append(text)
        if tag == "ul" and self.in_ings:
            self.in_ings = False
        if tag == "article" and self.in_recipe:
            self.recipes.append(
                {"id": self.recipe_id, "title": self.recipe_title or self.recipe_id or "?", "ings": self.current_ings}
            )
            self.in_recipe = False

    def handle_data(self, data):
        if self.in_h2:
            self.h2_buf.append(data)
        if self.in_li:
            self.li_buf.append(data)


def parse_recipes(path: Path) -> list[dict]:
    p = RecipeIngParser()
    p.feed(path.read_text(encoding="utf-8", errors="replace"))
    return p.recipes


def build_southern_db(recipes: list[dict]) -> dict:
    bucket: dict[str, dict] = {}
    for r in recipes:
        seen = set()
        for raw in r["ings"]:
            name = clean_ingredient(raw)
            if not name:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            if key not in bucket:
                bucket[key] = {
                    "id": re.sub(r"[^a-z0-9]+", "-", key).strip("-"),
                    "name": name,
                    "category": categorize(name),
                    "count": 0,
                    "examples": [],
                    "recipes": [],
                }
            e = bucket[key]
            e["count"] += 1
            if len(e["examples"]) < 3 and raw not in e["examples"]:
                e["examples"].append(raw)
            if len(e["recipes"]) < 12:
                e["recipes"].append({"id": r["id"], "title": r["title"]})
    ingredients = sorted(bucket.values(), key=lambda x: (-x["count"], x["name"].lower()))
    # notes
    for ing in ingredients:
        titles = ", ".join(x["title"] for x in ing["recipes"][:5])
        ing["note"] = f"Appears in {ing['count']} recipe(s). Examples: {titles}."
    equipment = [
        {"id": re.sub(r"[^a-z0-9]+", "-", n.lower()), "name": n, "blurb": b, "img": img}
        for img, n, b in SOUTHERN_EQUIP
    ]
    return {
        "book": "southern",
        "equipment": equipment,
        "featured": [{"img": i, "name": n, "blurb": b} for i, n, b in SOUTHERN_FEATURED],
        "ingredients": ingredients,
        "stats": {"recipes": len(recipes), "ingredients": len(ingredients), "equipment": len(equipment)},
    }


def build_chinese_db(recipes: list[dict]) -> dict:
    # Map curated names to recipe hits by fuzzy contains
    hits: dict[str, list] = defaultdict(list)
    raw_counter: Counter = Counter()
    for r in recipes:
        blob = " | ".join(r["ings"]).lower()
        for raw in r["ings"]:
            c = clean_ingredient(raw)
            if c:
                raw_counter[c.lower()] += 1
        for name, _cat, _note in CHINESE_CURATED:
            token = name.lower().split("(")[0].strip()
            # simple token match
            key = token
            if key in blob or any(tok in blob for tok in token.split()[:2] if len(tok) > 3):
                if len(hits[name]) < 10:
                    hits[name].append({"id": r["id"], "title": r["title"]})
    ingredients = []
    for name, cat, note in CHINESE_CURATED:
        recipes_hit = hits.get(name, [])
        # also count from cleaned raw if exact-ish
        count = max(len(recipes_hit), raw_counter.get(name.lower(), 0))
        if count == 0:
            count = 1  # still list as pantry staple
        ingredients.append(
            {
                "id": re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-"),
                "name": name,
                "category": cat,
                "count": count,
                "examples": [],
                "recipes": recipes_hit,
                "note": note + (f" Seen across ~{count} dishes in this book." if recipes_hit else " Core pantry staple for this kitchen."),
            }
        )
    ingredients.sort(key=lambda x: (-x["count"], x["name"].lower()))
    equipment = [
        {"id": re.sub(r"[^a-z0-9]+", "-", n.lower()), "name": n, "blurb": b, "img": img}
        for img, n, b in CHINESE_EQUIP
    ]
    return {
        "book": "chinese",
        "equipment": equipment,
        "featured": [{"img": i, "name": n, "blurb": b} for i, n, b in CHINESE_FEATURED],
        "ingredients": ingredients,
        "stats": {"recipes": len(recipes), "ingredients": len(ingredients), "equipment": len(equipment)},
    }


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


EXTRA_CSS = """
  /* Encyclopedia: Equipment + Ingredients DB */
  .ency-equip, .ency-ings {
    background: var(--paper, #fffaf3);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 2rem;
    border: 1px solid #e0c9a8;
    box-shadow: 0 12px 30px rgba(0,0,0,.18);
    padding: 0 0 1.5rem;
  }
  .ency-equip .ency-intro, .ency-ings .ency-intro {
    padding: 1.25rem 1.5rem 0.5rem;
    font-style: italic;
    color: #5a3a28;
    line-height: 1.5;
  }
  .ency-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1.25rem;
    padding: 0.5rem 1.5rem 0.5rem;
  }
  .ency-card {
    background: #fffaf3;
    border: 1px solid #e0c9a8;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(60,30,10,.08);
    display: flex;
    flex-direction: column;
  }
  .ency-card img {
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    display: block;
    background: #f0e6d4;
  }
  .ency-card .body { padding: 0.85rem 1rem 1.1rem; flex: 1; }
  .ency-card h4 { margin: 0 0 0.4rem; color: var(--deep, #3a2214); font-size: 1.05rem; line-height: 1.25; }
  .ency-card p { margin: 0; font-size: 0.9rem; color: #5a3a28; line-height: 1.45; }
  .ency-sub {
    margin: 1.25rem 1.5rem 0.75rem;
    color: var(--terracotta, #c4281c);
    font-size: 1.15rem;
    letter-spacing: .04em;
    text-transform: uppercase;
    border-bottom: 2px solid #e0c9a8;
    padding-bottom: 0.35rem;
  }
  .ing-controls {
    display: flex; flex-wrap: wrap; gap: .6rem; align-items: center;
    padding: .5rem 1.5rem 1rem;
  }
  .ing-controls input[type="search"] {
    flex: 1 1 220px; min-width: 180px;
    padding: .65rem .9rem; border: 1px solid #d2b48c; border-radius: 8px;
    font-size: 1rem; background: #fff;
  }
  .ing-chips { display: flex; flex-wrap: wrap; gap: .4rem; }
  .ing-chip {
    border: 1px solid #d2b48c; background: #fff8ee; color: #5a3a28;
    border-radius: 999px; padding: .35rem .75rem; font-size: .82rem; cursor: pointer;
  }
  .ing-chip.active, .ing-chip:hover { background: var(--terracotta, #c4281c); color: #fff; border-color: transparent; }
  .ing-stats { padding: 0 1.5rem .5rem; color: #7a5c3a; font-size: .9rem; }
  .ing-db {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem;
    padding: 0.25rem 1.5rem 1rem;
  }
  .ing-card {
    background: #fffdf8; border: 1px solid #e6d3b5; border-radius: 10px;
    padding: .9rem 1rem 1rem; display: flex; flex-direction: column; gap: .35rem;
  }
  .ing-card.hidden { display: none; }
  .ing-card .top { display: flex; justify-content: space-between; gap: .5rem; align-items: flex-start; }
  .ing-card h4 { margin: 0; font-size: 1.02rem; color: var(--deep, #3a2214); }
  .ing-badge {
    flex: 0 0 auto; font-size: .68rem; text-transform: uppercase; letter-spacing: .04em;
    background: #f3e2c8; color: #6a4020; border-radius: 999px; padding: .2rem .5rem; white-space: nowrap;
  }
  .ing-card .note { margin: 0; font-size: .88rem; color: #5a3a28; line-height: 1.4; }
  .ing-card .meta { font-size: .8rem; color: #8a6a48; }
  .ing-card .links { font-size: .82rem; line-height: 1.45; }
  .ing-card .links a { color: var(--terracotta, #c4281c); }
"""

ING_JS = """
<script>
(function(){
  function wire(rootId){
    var root = document.getElementById(rootId);
    if(!root) return;
    var search = root.querySelector('[data-ing-search]');
    var chips = root.querySelectorAll('[data-ing-chip]');
    var cards = root.querySelectorAll('.ing-card');
    var countEl = root.querySelector('[data-ing-count]');
    var activeCat = 'all';
    function apply(){
      var q = (search && search.value || '').toLowerCase().trim();
      var shown = 0;
      cards.forEach(function(c){
        var cat = c.getAttribute('data-cat') || '';
        var name = (c.getAttribute('data-name') || '').toLowerCase();
        var note = (c.getAttribute('data-note') || '').toLowerCase();
        var okCat = (activeCat === 'all' || cat === activeCat);
        var okQ = !q || name.indexOf(q) >= 0 || note.indexOf(q) >= 0 || cat.toLowerCase().indexOf(q) >= 0;
        var show = okCat && okQ;
        c.classList.toggle('hidden', !show);
        if(show) shown++;
      });
      if(countEl) countEl.textContent = shown + ' ingredients shown';
    }
    if(search) search.addEventListener('input', apply);
    chips.forEach(function(ch){
      ch.addEventListener('click', function(){
        chips.forEach(function(x){ x.classList.remove('active'); });
        ch.classList.add('active');
        activeCat = ch.getAttribute('data-ing-chip') || 'all';
        apply();
      });
    });
    apply();
  }
  wire('ingredients');
})();
</script>
"""


def render_equipment_section(db: dict, title: str, intro: str) -> str:
    cards = []
    for e in db["equipment"]:
        img = e.get("img")
        img_html = f'<img src="images/kit/{esc(img)}" alt="{esc(e["name"])}" loading="lazy" width="400" height="400"/>' if img else ""
        cards.append(
            f'<article class="ency-card">{img_html}<div class="body"><h4>{esc(e["name"])}</h4><p>{esc(e["blurb"])}</p></div></article>'
        )
    feat = []
    for f in db.get("featured") or []:
        feat.append(
            f'<article class="ency-card"><img src="images/kit/{esc(f["img"])}" alt="{esc(f["name"])}" loading="lazy" width="400" height="400"/><div class="body"><h4>{esc(f["name"])}</h4><p>{esc(f["blurb"])}</p></div></article>'
        )
    return f"""
  <section class="part" id="equipment">
    <h2>{esc(title)}</h2>
    <p>Full station map — tools first, then the pantry heroes that show up again and again.</p>
  </section>
  <div class="ency-equip" id="equipment-body">
    <p class="ency-intro">{esc(intro)}</p>
    <h3 class="ency-sub">Equipment</h3>
    <div class="ency-grid">
      {''.join(cards)}
    </div>
    <h3 class="ency-sub">Pantry Heroes</h3>
    <div class="ency-grid">
      {''.join(feat)}
    </div>
  </div>
"""


def render_ingredients_section(db: dict, title: str, intro: str) -> str:
    cats = sorted({i["category"] for i in db["ingredients"]})
    chips = ['<button type="button" class="ing-chip active" data-ing-chip="all">All</button>']
    for c in cats:
        chips.append(f'<button type="button" class="ing-chip" data-ing-chip="{esc(c)}">{esc(c)}</button>')
    cards = []
    for i in db["ingredients"]:
        links = ", ".join(
            f'<a href="#{esc(r["id"])}">{esc(r["title"])}</a>' for r in i.get("recipes") or []
        )
        cards.append(
            f'<article class="ing-card" data-cat="{esc(i["category"])}" data-name="{esc(i["name"])}" data-note="{esc(i.get("note",""))}">'
            f'<div class="top"><h4>{esc(i["name"])}</h4><span class="ing-badge">{esc(i["category"])}</span></div>'
            f'<p class="note">{esc(i.get("note",""))}</p>'
            f'<div class="meta">In {i["count"]} recipe(s)</div>'
            + (f'<div class="links">{links}</div>' if links else "")
            + "</article>"
        )
    return f"""
  <section class="part" id="ingredients">
    <h2>{esc(title)}</h2>
    <p>Searchable pantry database — every staple this book leans on.</p>
  </section>
  <div class="ency-ings" id="ingredients-body">
    <p class="ency-intro">{esc(intro)}</p>
    <div class="ing-controls">
      <input type="search" placeholder="Search ingredients…" data-ing-search aria-label="Search ingredients"/>
      <div class="ing-chips">{''.join(chips)}</div>
    </div>
    <div class="ing-stats"><span data-ing-count>{len(db['ingredients'])} ingredients shown</span> · {db['stats']['recipes']} recipes indexed</div>
    <div class="ing-db">
      {''.join(cards)}
    </div>
  </div>
"""


def inject(path: Path, db: dict, voice: str) -> None:
    text = path.read_text(encoding="utf-8")
    # CSS
    if "Encyclopedia: Equipment" not in text:
        text = text.replace("</style>", EXTRA_CSS + "\n  </style>", 1)
    # TOC Part 0
    toc_pat = re.compile(
        r"(<h3>Part 0[^<]*</h3>\s*<ol>)(.*?)(</ol>)",
        re.S | re.I,
    )
    toc_new = r"""\1
      <li><a href="#equipment">Equipment</a></li>
      <li><a href="#ingredients">Ingredients Database</a></li>
    \3"""
    text, n = toc_pat.subn(toc_new, text, count=1)
    if n == 0:
        print("WARN: TOC Part 0 not rewritten in", path)

    if voice == "southern":
        eq_title = "Part 0a — Equipment"
        eq_intro = "Children, you don't need a restaurant line. You need heavy pans, cold fat, a thermometer that tells the truth, and patience. Season the iron. Taste as you go."
        ing_title = "Part 0b — Ingredients Database"
        ing_intro = "Every onion, splash of buttermilk, and smoked turkey neck named in this book — searchable, filterable, and linked back to the recipes that love them."
    else:
        eq_title = "Part 0a — Wok Equipment"
        eq_intro = "A wok, a cleaver, a steamer, a spider, and a rice cooker will cook this whole book. High heat when you can get it; patience when you can't."
        ing_title = "Part 0b — Ingredients Database"
        ing_intro = "A Western-friendly Chinese and American-Chinese pantry: sauces, aromatics, starches, and proteins this book actually uses — no oddball organ aisle."

    new_blocks = render_equipment_section(db, eq_title, eq_intro) + render_ingredients_section(
        db, ing_title, ing_intro
    )

    # Replace encyclopedia (equipment + optional ingredients body) or legacy kit,
    # stopping at the next real chapter part (not equipment/ingredients).
    enc_re = re.compile(
        r'(?:'
        r'<section class="part" id="(?:kit|equipment)">.*?'
        r'(?:<section class="part" id="ingredients">.*?)?'
        r'(?:<div class="ency-ings"[^>]*>.*?)?'
        r')(?=<section class="part" id="(?!equipment|ingredients))',
        re.S,
    )
    if enc_re.search(text):
        text = enc_re.sub(new_blocks, text, count=1)
    else:
        m = re.search(r'<section class="part" id="(?!equipment|ingredients)[^"]+"', text)
        if m:
            text = text[:m.start()] + new_blocks + text[m.start():]
        else:
            text = text.replace('</body>', new_blocks + '\n</body>', 1)

    # JS once before </body>
    if "data-ing-search" in text and "wire('ingredients')" not in text:
        text = text.replace("</body>", ING_JS + "\n</body>", 1)
    elif "wire('ingredients')" not in text:
        text = text.replace("</body>", ING_JS + "\n</body>", 1)

    path.write_text(text, encoding="utf-8")
    print("Wrote", path, "ings", db["stats"]["ingredients"], "equip", db["stats"]["equipment"])


def main():
    # Southern
    s_root = ROOTS["southern"]
    s_recipes = parse_recipes(s_root / "index.html")
    s_db = build_southern_db(s_recipes)
    (s_root / "build").mkdir(exist_ok=True)
    (s_root / "build" / "pantry_db.json").write_text(json.dumps(s_db, indent=2), encoding="utf-8")
    inject(s_root / "index.html", s_db, "southern")

    # Chinese
    c_root = ROOTS["chinese"]
    c_recipes = parse_recipes(c_root / "index.html")
    c_db = build_chinese_db(c_recipes)
    (c_root / "build").mkdir(exist_ok=True)
    (c_root / "build" / "pantry_db.json").write_text(json.dumps(c_db, indent=2), encoding="utf-8")
    inject(c_root / "index.html", c_db, "chinese")

    print("DONE", json.dumps({"southern": s_db["stats"], "chinese": c_db["stats"]}))


if __name__ == "__main__":
    main()
