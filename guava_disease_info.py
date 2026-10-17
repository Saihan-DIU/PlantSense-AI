"""
Disease information and care instructions shown to farmers after a guava leaf
prediction. Class order MUST exactly match guava_model.CLASS_NAMES (alphabetical
folder order from training: Anthracnose, Dried, Healthy, Insect_Infestation,
Senescence, Sooty_Mould).
"""

DISEASE_INFO = {
    "Anthracnose": {
        "is_healthy": False,
        "description": (
            "A fungal disease (Colletotrichum gloeosporioides) causing dark, sunken, "
            "irregular brown-to-black lesions on leaves that can enlarge and cause "
            "premature leaf drop."
        ),
        "instructions": [
            "Remove and destroy infected leaves and fallen debris to reduce fungal spread.",
            "Apply a copper-based fungicide (e.g., copper oxychloride) or Mancozeb every 7-10 days.",
            "Avoid overhead irrigation; water at the base to keep foliage dry.",
            "Prune to improve air circulation and reduce humidity around the canopy.",
            "Remove and destroy severely infected branches during the dry season.",
        ],
    },
    "Dried": {
        "is_healthy": False,
        "description": (
            "Leaves showing drying/desiccation, usually from water stress, nutrient "
            "deficiency, root damage, or advanced untreated disease rather than a single pathogen."
        ),
        "instructions": [
            "Check soil moisture — both drought stress and waterlogged roots can cause leaf drying.",
            "Inspect roots and the base of the trunk for rot, pest damage, or girdling.",
            "Apply a balanced fertilizer if nutrient deficiency (e.g., nitrogen or potassium) is suspected.",
            "Mulch around the base to retain soil moisture and moderate soil temperature.",
            "If drying is localized to specific branches, prune them out and monitor for recurrence.",
        ],
    },
    "Healthy": {
        "is_healthy": True,
        "description": "No visible signs of disease, pest damage, or stress were detected on this leaf.",
        "instructions": [
            "Continue regular monitoring (2-3 times a week) for early signs of disease or pests.",
            "Maintain balanced fertilization (N-P-K) and consistent watering.",
            "Keep the field free of weeds and fallen debris.",
            "Practice proper spacing and pruning to maintain good air circulation.",
        ],
    },
    "Insect_Infestation": {
        "is_healthy": False,
        "description": (
            "Damage from sap-sucking or chewing insects (e.g., aphids, mealybugs, "
            "or leaf-feeding caterpillars), visible as holes, curling, discoloration, "
            "or visible pests on the leaf surface."
        ),
        "instructions": [
            "Identify the specific pest where possible — treatment differs between sucking and chewing insects.",
            "Spray neem oil or insecticidal soap, covering leaf undersides where pests often hide.",
            "Introduce or conserve natural predators such as ladybird beetles and lacewings.",
            "Remove and destroy heavily infested leaves or shoots.",
            "For severe infestations, apply a targeted insecticide per label directions, rotating modes of action to avoid resistance.",
        ],
    },
    "Senescence": {
        "is_healthy": False,
        "description": (
            "Natural leaf aging/senescence — older leaves yellowing and dying off as "
            "part of the plant's normal growth cycle, not caused by a pathogen."
        ),
        "instructions": [
            "This is typically a normal process; no fungicide or pesticide treatment is needed.",
            "Remove fallen senescent leaves from the field to reduce habitat for pests and secondary fungi.",
            "Ensure the plant is otherwise well-nourished so senescence isn't accelerated by nutrient stress.",
            "Monitor nearby leaves to confirm the pattern is age-related and not spreading like a disease.",
        ],
    },
    "Sooty_Mould": {
        "is_healthy": False,
        "description": (
            "A black, soot-like fungal coating growing on honeydew secreted by sap-sucking "
            "insects (aphids, mealybugs, scale). The mould itself rarely damages the leaf "
            "directly but blocks light and reduces photosynthesis."
        ),
        "instructions": [
            "Control the underlying sap-sucking insect population (aphids, mealybugs, or scale) — sooty mould will not clear up until the insects are managed.",
            "Wash affected leaves with a mild soap-water solution to remove the mould coating.",
            "Apply neem oil or insecticidal soap to target the honeydew-producing insects.",
            "Prune heavily affected branches to improve air circulation and light penetration.",
            "Monitor regularly, as sooty mould typically returns if the insect infestation isn't fully controlled.",
        ],
    },
}
