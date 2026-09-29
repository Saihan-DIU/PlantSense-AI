"""Disease information and treatment instructions shown to farmers after a prediction.

Class names/order MUST exactly match the order the model was trained on
(the order of the folders Keras's ImageDataGenerator/flow_from_directory picked up,
alphabetically, unless you passed a custom class list).
"""

CLASS_NAMES = [
    "Anthracnose of Papaya",
    "Healthy Leaf",
    "Mealybug Infestation",
    "Papaya Black Spot",
    "Papaya Mosaic Virus (PMV)",
    "Papaya Ring Spot Virus (PRSV)",
]

DISEASE_INFO = {
    "Anthracnose of Papaya": {
        "is_healthy": False,
        "description": (
            "A fungal disease (Colletotrichum gloeosporioides) causing dark, sunken, "
            "water-soaked spots on leaves and fruit that enlarge and merge over time."
        ),
        "instructions": [
            "Remove and destroy infected leaves and fallen fruit to reduce fungal spread.",
            "Apply a copper-based fungicide (e.g., copper oxychloride) or Mancozeb every 7-10 days.",
            "Avoid overhead irrigation; water at the base to keep foliage dry.",
            "Improve air circulation by proper plant spacing and pruning.",
            "Harvest fruit promptly and avoid mechanical injury during handling.",
        ],
    },
    "Healthy Leaf": {
        "is_healthy": True,
        "description": "No visible signs of disease or pest damage were detected on this leaf.",
        "instructions": [
            "Continue regular monitoring (2-3 times a week) for early signs of disease.",
            "Maintain balanced fertilization (N-P-K) and consistent watering.",
            "Keep the field free of weeds and fallen debris.",
            "Practice crop rotation and maintain proper spacing to prevent future outbreaks.",
        ],
    },
    "Mealybug Infestation": {
        "is_healthy": False,
        "description": (
            "Caused by sap-sucking mealybug insects that appear as small, white, cottony "
            "masses on leaves and stems, leading to yellowing, curling, and stunted growth."
        ),
        "instructions": [
            "Spray affected areas with neem oil or insecticidal soap, covering leaf undersides.",
            "Introduce natural predators such as ladybird beetles where possible.",
            "Prune and destroy heavily infested leaves/branches.",
            "Avoid excess nitrogen fertilizer, which encourages mealybug growth.",
            "For severe infestations, apply a systemic insecticide (e.g., imidacloprid) per label directions.",
        ],
    },
    "Papaya Black Spot": {
        "is_healthy": False,
        "description": (
            "A fungal disease (Asperisporium caricae) producing small, angular, black spots "
            "on the underside of leaves, eventually causing yellowing and leaf drop."
        ),
        "instructions": [
            "Remove and burn heavily spotted leaves to limit spore spread.",
            "Apply a protectant fungicide such as copper oxychloride or chlorothalonil.",
            "Ensure good field drainage and avoid overhead watering.",
            "Space plants adequately to reduce humidity around foliage.",
        ],
    },
    "Papaya Mosaic Virus (PMV)": {
        "is_healthy": False,
        "description": (
            "A viral disease causing mottled light/dark green mosaic patterns, leaf distortion, "
            "and stunted plant growth. Spread mainly by mechanical contact and contaminated tools."
        ),
        "instructions": [
            "Remove and destroy infected plants immediately to prevent spread — there is no cure.",
            "Disinfect pruning tools with bleach/alcohol between plants.",
            "Control aphid and other insect populations that can spread the virus.",
            "Use certified virus-free seeds/seedlings for new planting.",
            "Avoid working in the field when leaves are wet.",
        ],
    },
    "Papaya Ring Spot Virus (PRSV)": {
        "is_healthy": False,
        "description": (
            "One of the most destructive papaya viruses, spread by aphids, causing ring-shaped "
            "spots on fruit, mosaic mottling on leaves, and severe stunting."
        ),
        "instructions": [
            "Remove and destroy infected plants promptly to reduce the source of infection.",
            "Control aphid vectors using yellow sticky traps and approved insecticides.",
            "Plant resistant or tolerant papaya varieties if available in your region.",
            "Avoid planting new papaya near infected fields or cucurbit crops (alternate hosts).",
            "Use reflective mulches, which have been shown to reduce aphid landing rates.",
        ],
    },
}
