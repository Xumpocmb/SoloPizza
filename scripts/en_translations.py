"""English translations for the catalog fixture.

TRANSLATIONS is keyed by product slug and holds the values written into
name_en / description_en. CATEGORY_TRANSLATIONS follows the same rule.
Slugs missing from these dicts are reported by the applier instead of
being silently left empty.
"""

CATEGORY_TRANSLATIONS = {
    "picca": "Pizza",
    "fastfud": "Snacks",
    "burgery": "Burgers",
    "kombo": "Combo",
    "sety": "Sets",
    "napitki": "Drinks",
    "napitki-v-zal": "Drinks in the hall",
    "sousy": "Sauces",
    "skovorodki": "Hot dishes",
    "kalcone": "Calzone",
    "pivo": "Beer",
}

TRANSLATIONS = {
    # --- Комбо ---
    "kombo-ohota": (
        "Combo Hunt",
        "Includes:\r\nHunter's Pizza\r\nChicken Pizza\r\n\r\n1 L drink of your choice (please mention it in the order comment)",
    ),
    "kombo-sochnyj": (
        "Combo Juicy",
        "Includes:\r\nJuicy Burger Pizza\r\nHam and Mushroom Pizza\r\n\r\n1 L drink of your choice (please mention it in the order comment)",
    ),
    "kombo-shef": (
        "Combo Chef",
        "Includes:\r\nChef's Pizza 32 cm\r\nCountry Pizza 32 cm\r\nRanch Pizza 32 cm\r\n\r\n1 L drink of your choice (please mention it in the order comment)",
    ),
    # --- Пицца ---
    "ot-shefa": (
        "Chef's Choice",
        "Signature sauce, Mozzarella cheese, ham, bacon, Salami sausage, mushrooms, bell pepper, olives, onion",
    ),
    "sochnyj-burger": (
        "Juicy Burger",
        "Signature sauce, Mozzarella cheese, ham, bacon, pickled gherkins, onion, fresh tomato",
    ),
    "antaliya": (
        "Antalya",
        "Signature sauce, Mozzarella cheese, bacon, boiled and smoked sausage, fresh tomato, Parmesan cheese",
    ),
    "gavajskaya": (
        "Hawaiian",
        "Signature sauce, Mozzarella cheese, diced ham, chicken, canned pineapple",
    ),
    "yazyk-drakona": (
        "Dragon's Tongue",
        "Signature sauce, Mozzarella cheese, Salami sausage, fresh tomato, hunter's sausages, onion, Jalapeno pepper, Sriracha sauce",
    ),
    "lesnaya": (
        "Forest",
        "Signature sauce, Mozzarella cheese, chicken, bacon, mushrooms, pickled honey agarics, pickled onion",
    ),
    "derevenskaya": (
        "Country",
        "Signature sauce, Mozzarella cheese, bacon, Salami sausage, bell pepper, fresh tomato, onion, pickled gherkins, egg",
    ),
    "barbekyu": (
        "Barbecue",
        "Signature sauce, Mozzarella cheese, bacon, chicken, onion, bell pepper, barbecue sauce",
    ),
    "italyanskaya": (
        "Italian",
        "Signature sauce, Mozzarella cheese, bacon, diced ham, Salami sausage, mushrooms, olives, fresh tomato",
    ),
    "belluchi": (
        "Bellucci",
        "Signature sauce, Mozzarella cheese, hunter's sausages, boiled and smoked sausage, mushrooms, bell pepper",
    ),
    "zelyonyj-bum": (
        "Green Boom",
        "Signature sauce, Mozzarella cheese, mushrooms, bell pepper, onion, olives, cream cheese, fresh tomato",
    ),
    "chelentano": (
        "Chelentano",
        "Signature sauce, Mozzarella cheese, minced meat, Salami sausage, fresh tomato, onion, pickled cucumber",
    ),
    "soloneze": (
        "Soloneze",
        "Signature sauce, Mozzarella cheese, minced meat, bell pepper, mushrooms, chicken egg",
    ),
    "vetchina-s-gribami": (
        "Ham and Mushrooms",
        "Tomato sauce, Mozzarella cheese, classic ham, mushrooms, canned olives",
    ),
    "detskaya": (
        "Kids",
        "Signature sauce, Mozzarella cheese, diced ham, fresh tomato",
    ),
    "peperoni": (
        "Pepperoni",
        "Signature sauce, Mozzarella cheese, Salami sausage",
    ),
    "bombita": (
        "Bombita",
        "Signature sauce, Mozzarella cheese, mushrooms, boiled and smoked sausage, pickled cucumbers, chicken",
    ),
    "panskaya": (
        "Panska",
        "Signature sauce, Mozzarella sauce, Salami sausage, boiled and smoked sausage, ham, hunter's sausages",
    ),
    "kurinaya": (
        "Chicken",
        "Signature sauce, Mozzarella cheese, chicken, mushrooms, onion, fresh tomato",
    ),
    "mister-chiz": (
        "Mr. Cheese",
        "Signature sauce, Mozzarella cheese, Cheddar cheese, cream cheese, Parmesan cheese, Dorblu cheese",
    ),
    "chetyre-sezona": (
        "Four Seasons",
        "Signature sauce, Mozzarella cheese, Salami sausage, chicken, fresh tomato, ham, mushrooms, bacon, pickled gherkins, egg",
    ),
    "ohotnichya": (
        "Hunter's",
        "Signature sauce, Mozzarella cheese, hunter's sausages, bacon, mushrooms, pickled cucumbers, garlic sauce, teriyaki sauce",
    ),
    "myasnaya": (
        "Meat",
        "Signature sauce, Mozzarella cheese, Salami sausage, ham, bacon, hunter's sausages, fresh tomato, mushrooms, onion",
    ),
    "rancho": (
        "Ranch",
        "Signature sauce, Mozzarella cheese, bacon, chicken, fresh tomato, onion, garlic sauce",
    ),
    "kapperoni": (
        "Capperoni",
        "Signature sauce, Mozzarella sauce, capers, minced meat, boiled and smoked sausage, fresh tomato",
    ),
    "marinara": (
        "Marinara",
        "Signature sauce, Mozzarella cheese, seafood cocktail, bell pepper, olives, cream cheese",
    ),
    # --- Закуски ---
    "kartofel-fri": (
        "French Fries",
        "Juicy potato pieces fried to a golden crispy crust, a perfect addition to your favourite meal or snack. Enjoy the flavour of aromatic french fries cooked with love and carefully selected spices.",
    ),
    "kartofelnye-dolki": (
        "Potato Wedges",
        "Rich flavour of gently fried potato with a crispy golden crust. Our potato wedges are a perfect combination of a tender inside and a crispy outside. Enjoy every bite and savour the traditional taste in every piece.",
    ),
    "syrnyj-hvorost": (
        "Cheese Curly Fries",
        "A tempting snack that is sure to become your favourite treat. Our cheese curly fries are delicate strips of dough fried to a golden crispy crust and filled with the rich aroma of cheese. Dive into a world of incredible flavour and enjoy every piece of this unique delicacy.",
    ),
    "lukovye-kolca": (
        "Onion Rings",
        "Tender onion rings coated in a crunchy breading and fried to a golden caramelised crust. Our onion rings are a perfect combination of a tender inside and a crispy outside. Enjoy every bite of this appetising snack and treat yourself to a world of refined flavour.",
    ),
    "rebryshki-svinye": (
        "Pork Ribs",
        "The true embodiment of tenderness and juiciness - our pork ribs. Spicy and juicy, they are fried to a golden crispy crust, keeping the tenderness and the aroma of fresh spices. Enjoy every bite and savour an outstanding combination of flavours that will leave an unforgettable impression.",
    ),
    "naggetsy": (
        "Nuggets",
        "Rich flavour of tender chicken meat wrapped in a crispy golden coating. Our nuggets are a perfect combination of tenderness and crunch that will please your taste buds. Discover the aroma and the flavour of every bite and enjoy the unmatched pleasure of our nuggets.",
    ),
    "syrnye-palochki": (
        "Cheese Sticks",
        "Tender and fragrant cheese sticks - a perfect combination of delicate dough and rich cheese flavour. Fried to a golden crispy crust, they are excellent as a snack or an addition to any dish. Dive into a world of flavour with every bite and enjoy the distinctive aroma and taste of our cheese sticks.",
    ),
    "kartofelnye-oladi": ("Potato Pancakes", "Potato pancakes"),
    "krylyshki-kurinye": ("Chicken Wings", "Chicken wings"),
    "krylyshki-kurinye-ostrye": ("Spicy Chicken Wings", "Spicy chicken wings"),
    "shariki-kartofelnye": ("Potato Balls", "Potato balls"),
    # --- Бургеры ---
    "gamburger": (
        "Hamburger",
        "Bun, beef patty, pickled gherkins, burger sauce",
    ),
    "chizburger": (
        "Cheeseburger",
        "Bun, beef patty, Cheddar cheese, onion, pickled gherkins, burger sauce",
    ),
    "dvojnoj-chizburger": (
        "Double Cheeseburger",
        "Bun, 2 beef patties, Cheddar cheese x2, onion, pickled gherkins, burger sauce",
    ),
    "lanchburger": (
        "Lunch Burger",
        "Bun, beef patty, Cheddar cheese, Iceberg lettuce, selected chicken breast, onion, fresh tomato, burger sauce",
    ),
    "miksburger": (
        "Mix Burger",
        "Bun, chicken patty, Cheddar cheese, Iceberg lettuce, selected bacon, fresh tomato, burger sauce",
    ),
    "chiken-burger": (
        "Chicken Burger",
        "Bun, chicken patty, Iceberg lettuce, burger sauce",
    ),
    "chiken-spajsi": (
        "Spicy Chicken",
        "Bun, burger sauce, Iceberg lettuce, chicken patty, fresh tomato, jalapeno pepper, bacon, teriyaki sauce",
    ),
    "chiz-domashnij": (
        "Homestyle Cheese Burger",
        "Bun, burger sauce, Iceberg lettuce, beef patty, onion, fresh tomato, chicken egg",
    ),
    # --- Кальцоне ---
    "kalcone-s-salyami-i-opyatami": (
        "Calzone with Salami and Honey Agarics",
        "Signature sauce, Mozzarella cheese, Cremezzano cheese, Parmesan cheese, Salami sausage, pickled honey agarics, fresh tomato",
    ),
    "kalcone-s-farshem-i-percem": (
        "Calzone with Minced Meat and Pepper",
        "Signature sauce, Mozzarella cheese, minced meat, bell pepper, onion",
    ),
    "kalcone-s-vetchinoj-i-tomatami": (
        "Calzone with Ham and Tomatoes",
        "Signature sauce, Mozzarella cheese, diced ham, Parmesan cheese, Cheddar cheese, onion, fresh tomato",
    ),
    "kalcone-sytnaya": (
        'Calzone "Hearty"',
        "Signature sauce, bacon, Salami sausage, onion, Mozzarella cheese, pickled honey agarics, pickled cucumbers",
    ),
    "kalcone-barbekyu": (
        'Calzone "Barbecue"',
        "Signature sauce, fresh tomato, hunter's sausages, Mozzarella cheese, barbecue sauce",
    ),
    "kalcone-kukuruzka": (
        'Calzone "Corn"',
        "Signature sauce, Mozzarella cheese, boiled and smoked sausage, bacon, canned corn, onion",
    ),
    # --- Соусы ---
    "syrnyj": (
        "Cheese",
        "Enjoy the excellent combination of a delicate creamy flavour with rich cheese notes in every sip of Heinz cheese sauce. A perfect addition to your favourite dishes, it enhances their taste and makes them even richer and more aromatic. Discover a new level of pleasure with our Heinz cheese sauce.",
    ),
    "ketchup": (
        "Ketchup",
        "Revive your taste experience with our classic Heinz ketchup. The rich flavour of ripe tomatoes seasoned with delicate spices gives your dishes an unmatched aroma and a bright taste. This perfect extra ingredient will lift the mood at your table and make every meal unforgettable.",
    ),
    "burger-sous": (
        "Burger Sauce",
        "Discover the perfect addition to your burgers with our burger sauce. The combination of the tenderness of mayonnaise, notes of tomato sauce and a pleasant spiciness makes this sauce an ideal choice for lovers of juicy burgers. Dive into a world of rich flavour and add an unmatched aroma to your favourite dishes with our burger sauce.",
    ),
    "teriyaki": (
        "Teriyaki",
        "Discover the magic of flavour with our teriyaki sauce. A refined combination of soy sauce, natural honey and aromatic spices creates an unmatched aroma and a rich taste. Enjoy the harmony of sweetness and spiciness that will enhance the flavour of every dish. Dive into the world of eastern flavours with our teriyaki sauce.",
    ),
    "chesnochnyj": (
        "Garlic",
        "Revive your dishes with our fragrant garlic sauce. A delicate combination of fresh garlic, creamy mayonnaise and a light tang gives your dishes an unmatched flavour and aroma. Enjoy the richness of flavour and add a highlight to every meal with our garlic sauce.",
    ),
    "sous-barbekyu": (
        "Barbecue",
        "Discover the perfect combination of sweetness and spiciness with our barbecue sauce. The rich tomato flavour enriched with the aroma of caramelised sugar and notes of aromatic spices makes this sauce an essential addition to your dishes. Enjoy the harmony of flavours and create a real feast for your taste with our barbecue sauce.",
    ),
    "svit-chili": (
        "Sweet Chilli",
        "Revive your taste experience with our sweet chilli sauce. The combination of the bright sweetness of ripe peppers and the heat of chilli creates an unmatched flavour that will win you over. Enjoy the aroma and the spiciness of every sip and add a touch of passion to your dishes with our sweet chilli sauce.",
    ),
    "salsa": (
        "Salsa",
        "Travel to Mexico with our fresh and fragrant salsa. The juicy combination of ripe tomatoes, crunchy onion, aromatic pepper and fresh herbs creates an unmatched flavour that will give you a real festival of tastes. Enjoy the bright notes, perfect for traditional Mexican dishes or as inspiration for your own culinary experiments.",
    ),
    # --- Напитки ---
    "kislo-sladkij": ("Sweet and Sour", "Sweet and sour"),
    "fanta": ("Fanta", "Fanta"),
    "sprite": ("Sprite", "Sprite"),
    "coca-cola-classic": ("Coca Cola Classic", "Coca Cola Classic"),
    "bonaqua-negazirovannaya": ("Bonaqua Still", "Bonaqua still"),
    "bonaqua-gazirovannaya": ("Bonaqua Sparkling", "Bonaqua sparkling"),
    "sok-dobryj": ("Dobry Juice", None),
    "sok-rich": ("Rich Juice", "Rich juice"),
    "schweppes": ("Schweppes", "Schweppes"),
    "pepsi": ("Pepsi", "Pepsi"),
    "alivariya-0": ("Alivaria 0", "Alivaria 0"),
    "alivariya-10-ka": ("Alivaria 10-KA", "Alivaria 10-KA"),
    "zalatoe": ("Zalatoe", "Zalatoe"),
    "zhaceckij-gus": ("Zhatseckiy Gus", "Zhatseckiy Gus"),
    "porter": ("Porter", "Porter"),
    "pitnae": ("Pitnoe", "Pitnoe"),
    "bagemskoe": ("Bagemskoe", "Bagemskoe"),
    "tuborg": ("Tuborg", "Tuborg"),
    "blank": ("Blank", None),
    "garazh-mandarin": ("Garage Assorted", "Garage new"),
    "blank-rozovyj": ("Blank Pink", None),
    "pshenichnoe": ("Wheat", None),
    "kvas-razlivnoj": ("Draft Kvass", "Draft kvass"),
    "pivo-razlivnoe": ("Draft Beer", "Draft beer"),
    "aura-negazirovannaya": ("Aura Still", "Aura still"),
    "aura-gazirovannaya": ("Aura Sparkling", "Aura sparkling"),
    "mirinda": ("Mirinda", "Mirinda"),
    "rich-tea": ("Rich Tea", "Rich tea"),
    "pulpy": ("Pulpy", "Pulpy"),
    "ipa-ipa-mango": ("APA", "IPA - IPA MANGO"),
    "molochnyj-koktejl": ("Milkshake", "Milkshake"),
    "chaj-v-assortimente": ("Assorted Tea", "Tea assortment"),
    "espresso": ("Espresso", "Espresso"),
    "kapuchino": ("Cappuccino", "Cappuccino"),
    "flet-vajt": ("Flat White", "Flat White"),
    "amerikano": ("Americano", "Americano"),
    "latte": ("Latte", "Latte"),
    "morozhennoe": ("Ice Cream", "Ice cream assortment"),
    "topping": ("Topping", "Topping"),
    "aksamitnae-lidskae-tyomnoe": (
        "Aksamitnaye Lidskoye Dark",
        "Aksamitnaye Lidskoye Dark",
    ),
    "lidskae-zimovae": ("Lidskoye Zimovaye", "Lidskoye Zimovaye"),
    "lidskae-nulyovka": ("Lidskoye Nulyovka", "Lidskoye Nulyovka"),
    "lidskae-lid-bir-fresh": ("Lidskoye Lid Beer Fresh", "Lidskoye Lid Beer Fresh"),
    "lidskae-koronet-lager": ("Lidskoye Koronet Lager", "Lidskoye Koronet Lager"),
    "lidskae-rocky-crok": ("Lidskoye Rocky Crok", "Lidskoye Rocky Crok"),
    "lidskae-majstr-vecher-v-bryugge": (
        "Lidskoye Meister Evening in Bruges",
        "Lidskoye Meister Evening in Bruges",
    ),
    "lidskae-majstr-pshenichnoe": (
        "Lidskoye Meister Wheat",
        "Lidskoye Meister Wheat",
    ),
    "chajnichek": ("Tea in a Teapot", "600 ml teapot"),
    "lidskae-premium": ("Lidskoye Premium", "Lidskoye Premium"),
    "lidskae-pilsner": ("Lidskoye Pilsner", "Lidskoye Pilsner"),
    "alivariya-kalyadny-cud": (
        "Alivaria Kalyadny Tsud",
        "Alivaria Kalyadny Tsud",
    ),
    "alivariya-temnoe": ("Alivaria Dark", "Alivaria Dark"),
    "burn-original": ("Burn Original", None),
    "coca-cola-zero": ("Coca Cola Zero", None),
    "nektar-dobryj": ("Nektar Dobry", None),
    # --- Горячие блюда / сковородки ---
    "skovorodka-s-dranikami-i-bedryshkami": (
        "Skillet with Pancakes and Drumsticks",
        "Onion, bacon, semi-finished potato pancakes, sour cream, chicken drumsticks, Mozzarella cheese, chicken egg",
    ),
    "skovorodka-s-dranikami-i-kolbaskami": (
        "Skillet with Pancakes and Sausages",
        "Onion, bacon, semi-finished potato pancakes, sour cream, Polesian sausages, chicken egg",
    ),
    "skovorodka-s-dolkami-i-bedryshkami": (
        "Skillet with Wedges and Drumsticks",
        "Onion, bacon, potato wedges, chicken drumsticks, Mozzarella cheese, chicken egg",
    ),
    "skovorodka-s-dolkami-i-kolbaskami": (
        "Skillet with Wedges and Sausages",
        "Onion, bacon, potato wedges, Polesian sausages, chicken egg",
    ),
    "rich-chaj": (
        "Rich Tea",
        "Non-alcoholic still beverage with a flavour of",
    ),
    "belae-zolata": ("Alivaria White Gold", "Alivaria White Gold"),
    "krevetki-v-tempure": ("Shrimp in Tempura", "Shrimp in tempura"),
    "garazh-ba": ("Garage Non-Alcoholic", "Garage"),
    "lidskae-yantarnoe": ("Lidskoye Amber", "Lidskoye Amber"),
    "majstra-indian-pejl-el": ("Meister Indian Pale Ale", "Meister Indian Pale Ale"),
    "assorti": (
        "Assorted",
        "Shrimp \r\nChicken \r\nJalapeno \r\nPineapple \r\nTomato \r\nSignature sauce \r\nMozzarella cheese",
    ),
    "ekzotik": (
        "Exotic",
        "Mozzarella cheese, Dorblu cheese, cream cheese, fresh pear, maple syrup",
    ),
    "mone": (
        "Mone",
        "Signature sauce, Mozzarella cheese, classic ham, hunter's sausages, bell pepper, breaded onion, Parmesan sauce",
    ),
    "lahmadzhun": ("Lahmacun", "Turkish minced meat, Iceberg lettuce, Parmesan cheese"),
    "sochnaya": (
        "Juicy",
        "Signature sauce, Mozzarella cheese, Turkish minced meat, hunter's sausages, fresh tomato, bell pepper, breaded onion, egg, barbecue sauce",
    ),
    "kvas-temnyj": ("Dark Kvass", None),
    "kvas-svetlyj": ("Light Kvass", None),
    "smetana": ("Sour Cream", "Sour cream"),
    "flash-energetik": ("Flash Energy Drink", "Flash energy drink"),
    "red-ale": ("Red Ale", "Red Ale"),
    "myasnaya-simfoniya": (
        "Meat Symphony",
        "Signature sauce, Mozzarella cheese, smoked sausage, hunter's sausages, chicken, fresh tomato, pickled cucumbers, onion, mustard sauce",
    ),
    # --- Сеты ---
    "sprint": (
        "Sprint Set",
        "Hamburger 1 pc.\r\nFrench fries 60 g\r\nKetchup sauce 1 pc.\r\nCoca-Cola 0.33 L",
    ),
    "detskij": (
        "Kids Set",
        "Chicken burger 1 pc.\r\nFrench fries 60 g\r\nKetchup sauce 1 pc.\r\nJuice 0.2 L",
    ),
    "mini-set": (
        "Mini Set",
        "Nuggets 5 pcs\r\nPotato balls 100 g\r\nKetchup sauce 1 pc.",
    ),
    "ddlya-dvoih": (
        "Set for Two",
        "Onion rings 4 pcs\r\nFrench fries 80 g\r\nChicken wings 4 pcs\r\nCheese sticks 4 pcs\r\nPotato balls 100 g\r\nKetchup sauce\r\nGarlic sauce",
    ),
    "dlya-kompanii": (
        "Set for a Company",
        "Potato wedges 160 g\r\nChicken wings 7 pcs\r\nOnion rings 5 pcs\r\nHunter's sausages 110 g\r\nLightly salted cucumbers 50 g\r\nCheese curly fries 80 g\r\nShrimp in tempura 3 pcs\r\nGarlic sauce 1 pc.\r\nKetchup sauce 1 pc.\r\nMustard sauce 1 pc.",
    ),
    "enerdzhi": (
        "Energy Set",
        "Onion rings 8 pcs\r\nNuggets 9 pcs\r\nPork ribs 255 g\r\nGarlic sauce 1 pc.\r\nBarbecue sauce 1 pc.",
    ),
    "maksimum": (
        "Maximum Set",
        "Pork ribs 325 g\r\nCheese sticks 4 pcs\r\nChicken wings 5 pcs\r\nDrumstick 120 g\r\nPotato pancakes 4 pcs\r\nKetchup sauce 1 pc.\r\nGarlic sauce 1 pc.\r\nBarbecue sauce 1 pc.",
    ),
    "holodnyj-koktejl": ("Cold Cocktail", "Bonaqua or 7UP, lemon, mint, syrup"),
}
