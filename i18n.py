"""English / Bangla (বাংলা) interface text.

Every visible string in the templates and in static/js comes from STRINGS,
as t("key", **placeholders). Disease names, descriptions and treatment steps
live in disease_info.py / guava_disease_info.py (English) and
disease_info_bn.py (Bangla).

URLs: English pages live at / and /guava, Bangla pages at /bn/ and /bn/guava.
"""
from markupsafe import Markup

import disease_info
import disease_info_bn
import guava_disease_info

LANGS = ("en", "bn")
DEFAULT_LANG = "en"

# key: (English, Bangla). Values may contain {placeholders}; keys ending in
# ".html" contain markup and are rendered unescaped.
STRINGS = {
    # Meta / page titles
    "meta.description": (
        "PlantSense AI detects plant leaf diseases from a single photo and gives practical treatment steps.",
        "PlantSense AI একটি ছবি থেকেই গাছের পাতার রোগ শনাক্ত করে এবং করণীয় জানিয়ে দেয়।",
    ),
    "title.home": ("{Crop} Leaf Disease Detection — PlantSense AI", "{Crop} পাতার রোগ শনাক্তকরণ — PlantSense AI"),
    "title.result": ("{label} — {Crop} Diagnosis · PlantSense AI", "{label} — {Crop} রোগ নির্ণয় · PlantSense AI"),
    "skip": ("Skip to content", "মূল অংশে যান"),

    # Crops
    "crop.papaya": ("papaya", "পেঁপে"),
    "crop.guava": ("guava", "পেয়ারা"),
    "crop.Papaya": ("Papaya", "পেঁপে"),
    "crop.Guava": ("Guava", "পেয়ারা"),
    "crop.Tomato": ("Tomato", "টমেটো"),
    "crop.tomato": ("tomato", "টমেটো"),

    # Navbar
    "nav.how": ("How it works", "কীভাবে কাজ করে"),
    "nav.features": ("Features", "বৈশিষ্ট্য"),
    "nav.about": ("About", "আমাদের সম্পর্কে"),
    "nav.select_crop": ("Select crop", "ফসল বাছাই করুন"),
    "nav.conditions": ("6 leaf conditions", "৬টি পাতার অবস্থা"),
    "nav.in_development": ("In development", "তৈরি হচ্ছে"),
    "nav.live": ("Live", "চালু"),
    "nav.soon": ("Soon", "শীঘ্রই"),
    "nav.cta": ("Diagnose a leaf", "পাতা পরীক্ষা করুন"),
    "nav.open_menu": ("Open menu", "মেনু খুলুন"),
    "nav.close_menu": ("Close menu", "মেনু বন্ধ করুন"),
    "lang.label": ("Language", "ভাষা"),
    "nav.primary": ("Primary", "প্রধান মেনু"),
    "result.breadcrumb": ("Breadcrumb", "অবস্থান"),

    # Hero
    "hero.eyebrow": ("AI plant health assistant", "এআই উদ্ভিদ স্বাস্থ্য সহকারী"),
    "hero.title.html": (
        'Detect {crop} leaf diseases <span class="text-accent">in seconds.</span>',
        '{Crop} পাতার রোগ শনাক্ত করুন <span class="text-accent">মুহূর্তেই।</span>',
    ),
    "hero.lead": (
        "Upload a clear photo of a {crop} leaf and get an instant AI diagnosis with step-by-step "
        "treatment guidance — built for farmers, free to use.",
        "{Crop} পাতার একটি পরিষ্কার ছবি দিন, আর সাথে সাথে পেয়ে যান এআই-এর রোগ নির্ণয় ও ধাপে ধাপে "
        "চিকিৎসার পরামর্শ — কৃষকদের জন্য তৈরি, সম্পূর্ণ বিনামূল্যে।",
    ),
    "hero.stat.conditions": ("Conditions", "রোগের ধরন"),
    "hero.stat.time": ("Analysis time", "বিশ্লেষণের সময়"),
    "hero.stat.time_value": ("< 5s", "< ৫ সেকেন্ড"),
    "hero.stat.cost": ("Cost", "খরচ"),
    "hero.stat.free": ("Free", "বিনামূল্যে"),
    "hero.trust.signup": ("No signup required", "সাইন আপ লাগবে না"),
    "hero.trust.phone": ("Works on any phone", "যেকোনো ফোনে চলে"),
    "hero.trust.steps": ("Treatment steps included", "চিকিৎসার ধাপসহ"),

    # Upload card
    "upload.title": ("Analyze a {crop} leaf", "{Crop} পাতা পরীক্ষা করুন"),
    "upload.formats": ("JPG, PNG, HEIC, WEBP & more · up to {mb} MB", "JPG, PNG, HEIC, WEBP ও আরও · সর্বোচ্চ {mb} MB"),
    "upload.on_device": ("Runs on your device", "আপনার ডিভাইসেই চলে"),
    "upload.online": ("Model online", "মডেল চালু"),
    "upload.click.html": ("<strong>Click to upload</strong> or drag and drop", "<strong>ছবি বাছাই করুন</strong> অথবা এখানে টেনে আনুন"),
    "upload.hint": ("A single, well-lit leaf works best", "ভালো আলোতে একটি পাতার ছবি সবচেয়ে ভালো কাজ করে"),
    "upload.preview_alt": ("Selected leaf preview", "বাছাই করা পাতার ছবি"),
    "upload.change": ("Change photo", "ছবি বদলান"),
    "upload.analyze": ("Analyze leaf", "পাতা বিশ্লেষণ করুন"),
    "upload.preparing_model": ("Preparing the AI model…", "এআই মডেল প্রস্তুত হচ্ছে…"),
    "upload.privacy": ("Your photo is analyzed on this device and never uploaded.", "আপনার ছবি এই ডিভাইসেই বিশ্লেষণ হয়, কোথাও আপলোড হয় না।"),
    "upload.tips": ("Photo tips", "ছবি তোলার পরামর্শ"),
    "tip.daylight": ("Natural daylight.", "দিনের আলোয়।"),
    "tip.daylight_text": ("Avoid heavy shadows.", "গাঢ় ছায়া এড়িয়ে চলুন।"),
    "tip.frame": ("Fill the frame.", "পাতা বড় করে তুলুন।"),
    "tip.frame_text": ("Center one leaf.", "একটি পাতা মাঝখানে রাখুন।"),
    "tip.background": ("Plain background.", "সাদামাটা পটভূমি।"),
    "tip.background_text": ("One leaf, plain surface.", "সমতল জায়গায় একটি পাতা।"),
    "tip.sharp": ("Keep it sharp.", "ছবি স্পষ্ট রাখুন।"),
    "tip.sharp_text": ("No blur or glare.", "ঝাপসা বা চকচকে নয়।"),

    # How it works
    "how.eyebrow": ("Process", "পদ্ধতি"),
    "how.title": ("From photo to diagnosis in three steps", "ছবি থেকে রোগ নির্ণয়, মাত্র তিন ধাপে"),
    "how.lead.browser": (
        "No lab, no waiting for an expert visit. Everything runs right in your browser, in a few seconds.",
        "ল্যাব লাগবে না, বিশেষজ্ঞের অপেক্ষাও নয়। সবকিছু আপনার ব্রাউজারেই চলে, মাত্র কয়েক সেকেন্ডে।",
    ),
    "how.lead.server": (
        "No lab, no waiting for an expert visit. Results arrive in a few seconds.",
        "ল্যাব লাগবে না, বিশেষজ্ঞের অপেক্ষাও নয়। ফলাফল আসে কয়েক সেকেন্ডেই।",
    ),
    "how.step1": ("Upload a photo", "ছবি দিন"),
    "how.step1_text": ("Take a clear photo of the {crop} leaf with your phone and upload it.", "ফোনে {crop} পাতার একটি পরিষ্কার ছবি তুলে আপলোড করুন।"),
    "how.step2": ("AI analyzes it", "এআই বিশ্লেষণ করে"),
    "how.step2_text.papaya": (
        "A MaxViT vision transformer scans the leaf for visual signs of disease in seconds.",
        "MaxViT ভিশন ট্রান্সফরমার মডেল কয়েক সেকেন্ডে পাতায় রোগের লক্ষণ খুঁজে দেখে।",
    ),
    "how.step2_text.guava": (
        "A ConvNeXtV2 + attention model scans the leaf for visual signs of disease in seconds.",
        "ConvNeXtV2 + অ্যাটেনশন মডেল কয়েক সেকেন্ডে পাতায় রোগের লক্ষণ খুঁজে দেখে।",
    ),
    "how.step3": ("Get your diagnosis", "ফলাফল দেখুন"),
    "how.step3_text": (
        "See the detected condition, a confidence score, and practical treatment steps.",
        "শনাক্ত হওয়া রোগ, নিশ্চয়তার হার এবং করণীয় ধাপগুলো দেখুন।",
    ),

    # Features
    "feat.eyebrow": ("Why PlantSense", "কেন PlantSense"),
    "feat.title": ("Built for the field, not the lab", "ল্যাবের জন্য নয়, মাঠের জন্য তৈরি"),
    "feat.lead": (
        "Designed around how farmers actually work: a phone, a leaf, and a decision to make today.",
        "কৃষকের আসল কাজের ধরন মাথায় রেখে তৈরি: একটি ফোন, একটি পাতা, আর আজই নেওয়ার মতো একটি সিদ্ধান্ত।",
    ),
    "feat.instant": ("Instant results", "তাৎক্ষণিক ফলাফল"),
    "feat.instant_text": (
        "Get a diagnosis in seconds instead of waiting days for an expert visit — act before the disease spreads.",
        "বিশেষজ্ঞের জন্য দিনের পর দিন অপেক্ষা নয় — কয়েক সেকেন্ডেই রোগ নির্ণয়, রোগ ছড়ানোর আগেই ব্যবস্থা নিন।",
    ),
    "feat.conditions": ("Detectable conditions", "শনাক্তযোগ্য রোগসমূহ"),
    "cond.anthracnose": ("Anthracnose", "অ্যানথ্রাকনোজ"),
    "cond.black_spot": ("Black spot", "কালো দাগ"),
    "cond.mealybug": ("Mealybug", "মিলিবাগ"),
    "cond.mosaic": ("Mosaic virus", "মোজাইক ভাইরাস"),
    "cond.ring_spot": ("Ring spot virus", "রিং স্পট ভাইরাস"),
    "cond.healthy": ("Healthy", "সুস্থ"),
    "feat.trained": ("Trained on real leaves", "আসল পাতায় প্রশিক্ষিত"),
    "feat.trained_text": ("Recognizes 6 common papaya conditions, including healthy leaves.", "সুস্থ পাতাসহ পেঁপের ৬টি সাধারণ অবস্থা চিনতে পারে।"),
    "feat.treatment": ("Actionable treatment", "কার্যকর চিকিৎসা"),
    "feat.treatment_text": (
        "Every result comes with clear, practical steps you can act on today.",
        "প্রতিটি ফলাফলের সাথে থাকে স্পষ্ট, বাস্তবসম্মত করণীয় — আজই কাজে লাগাতে পারবেন।",
    ),
    "feat.device": ("Works on any device", "যেকোনো ডিভাইসে চলে"),
    "feat.device_text": (
        "Use it from a phone in the field or a computer at home. No app install.",
        "মাঠে ফোন থেকে বা বাসায় কম্পিউটার থেকে ব্যবহার করুন। কোনো অ্যাপ ইনস্টল লাগবে না।",
    ),
    "feat.free": ("Free and open", "বিনামূল্যে, সবার জন্য"),
    "feat.free_text": ("No signup, no subscription. Upload a photo and get help.", "সাইন আপ নেই, সাবস্ক্রিপশন নেই। ছবি দিন, সাহায্য নিন।"),

    # About
    "about.eyebrow": ("About us", "আমাদের সম্পর্কে"),
    "about.title": ("Research-driven, farmer-focused", "গবেষণাভিত্তিক, কৃষককেন্দ্রিক"),
    "about.p1": (
        "We are a team of Computer Science & Engineering students from Dhaka International University "
        "working on Artificial Intelligence, Machine Learning, Computer Vision, and Smart Agriculture.",
        "আমরা ঢাকা ইন্টারন্যাশনাল ইউনিভার্সিটির কম্পিউটার সায়েন্স অ্যান্ড ইঞ্জিনিয়ারিং বিভাগের একদল শিক্ষার্থী। "
        "আমরা কাজ করি কৃত্রিম বুদ্ধিমত্তা, মেশিন লার্নিং, কম্পিউটার ভিশন ও স্মার্ট কৃষি নিয়ে।",
    ),
    "about.p2": (
        "We built this platform to explore how modern AI can be applied to real agricultural problems. "
        "Our goal is to make plant disease detection simple, accessible, and easy to understand.",
        "আধুনিক এআই কীভাবে বাস্তব কৃষি সমস্যায় কাজে লাগানো যায়, তা খুঁজে দেখতেই আমরা এই প্ল্যাটফর্মটি তৈরি করেছি। "
        "আমাদের লক্ষ্য গাছের রোগ শনাক্তকরণকে সহজ, সবার নাগালে এবং সহজবোধ্য করা।",
    ),
    "tag.ai": ("Artificial Intelligence", "কৃত্রিম বুদ্ধিমত্তা"),
    "tag.ml": ("Machine Learning", "মেশিন লার্নিং"),
    "tag.cv": ("Computer Vision", "কম্পিউটার ভিশন"),
    "tag.agri": ("Smart Agriculture", "স্মার্ট কৃষি"),
    "team.role": ("Researcher & Developer", "গবেষক ও ডেভেলপার"),
    "team.org": ("Dept. of CSE, Dhaka International University", "সিএসই বিভাগ, ঢাকা ইন্টারন্যাশনাল ইউনিভার্সিটি"),
    "team.photo_alt": ("Portrait of {name}", "{name}-এর ছবি"),
    "team.linkedin_aria": ("{name} on LinkedIn (opens in a new tab)", "LinkedIn-এ {name} (নতুন ট্যাবে খুলবে)"),

    # CTA band
    "cta.title": ("Have a sick-looking leaf?", "পাতায় রোগের লক্ষণ দেখছেন?"),
    "cta.text": ("Get a diagnosis and treatment plan in under a minute.", "এক মিনিটের মধ্যেই রোগ নির্ণয় ও চিকিৎসার পরিকল্পনা পান।"),

    # Result
    "result.back": ("{Crop} diagnosis", "{Crop} রোগ নির্ণয়"),
    "result.crumb": ("Result", "ফলাফল"),
    "result.image_alt": ("Uploaded {crop} leaf", "আপলোড করা {crop} পাতা"),
    "result.caption": ("Uploaded photo", "আপলোড করা ছবি"),
    "result.another": ("Analyze another leaf", "আরেকটি পাতা পরীক্ষা করুন"),
    "result.print": ("Print report", "রিপোর্ট প্রিন্ট করুন"),
    "result.healthy": ("Healthy leaf", "সুস্থ পাতা"),
    "result.disease": ("Disease detected", "রোগ শনাক্ত হয়েছে"),
    "result.confidence": ("confidence", "নিশ্চয়তা"),
    "result.confidence_aria": ("Confidence {value} percent", "নিশ্চয়তা {value} শতাংশ"),
    "result.lowconf.html": (
        "<strong>Low confidence.</strong> The model isn't sure about this one. Try a sharper photo of a "
        "single leaf in daylight, and confirm with a local expert.",
        "<strong>নিশ্চয়তা কম।</strong> মডেলটি এই ছবির ব্যাপারে নিশ্চিত নয়। দিনের আলোয় একটি পাতার আরও "
        "স্পষ্ট ছবি দিয়ে আবার চেষ্টা করুন, এবং একজন স্থানীয় বিশেষজ্ঞের সাথে মিলিয়ে নিন।",
    ),
    "result.care": ("Care recommendations", "যত্নের পরামর্শ"),
    "result.actions": ("Recommended actions", "করণীয়"),
    "result.breakdown": ("Prediction breakdown", "পূর্বাভাসের বিস্তারিত"),
    "result.breakdown_sub": ("Top {n} classes by model probability", "মডেলের সম্ভাবনা অনুযায়ী শীর্ষ {n}টি ফলাফল"),
    "result.disclaimer": (
        "AI predictions can be wrong. Consult a qualified agricultural expert before large-scale treatment.",
        "এআই-এর পূর্বাভাস ভুল হতে পারে। বড় পরিসরে চিকিৎসার আগে একজন অভিজ্ঞ কৃষি বিশেষজ্ঞের পরামর্শ নিন।",
    ),

    # Footer
    "footer.about": (
        "AI-powered plant leaf disease detection, developed as an academic research project applying "
        "computer vision to real-world smart agriculture.",
        "এআই-চালিত গাছের পাতার রোগ শনাক্তকরণ — বাস্তব স্মার্ট কৃষিতে কম্পিউটার ভিশন প্রয়োগের "
        "একটি একাডেমিক গবেষণা প্রকল্প।",
    ),
    "footer.product": ("Product", "সেবাসমূহ"),
    "footer.papaya": ("Papaya diagnosis", "পেঁপে রোগ নির্ণয়"),
    "footer.guava": ("Guava diagnosis", "পেয়ারা রোগ নির্ণয়"),
    "footer.institution": ("Institution", "প্রতিষ্ঠান"),
    "footer.dept": ("Department of Computer Science & Engineering", "কম্পিউটার সায়েন্স অ্যান্ড ইঞ্জিনিয়ারিং বিভাগ"),
    "footer.university": ("Dhaka International University", "ঢাকা ইন্টারন্যাশনাল ইউনিভার্সিটি"),
    "footer.disclaimer": ("Disclaimer", "সতর্কতা"),
    "footer.disclaimer_text": (
        "Always consult a qualified local agricultural expert to confirm a diagnosis before large-scale treatment.",
        "বড় পরিসরে চিকিৎসা শুরুর আগে সবসময় একজন অভিজ্ঞ স্থানীয় কৃষি বিশেষজ্ঞের সাথে পরামর্শ করে রোগ নিশ্চিত করুন।",
    ),
    "footer.copyright": ("© {year} PlantSense AI · Dhaka International University", "© {year} PlantSense AI · ঢাকা ইন্টারন্যাশনাল ইউনিভার্সিটি"),
    "footer.tagline": ("Built for academic research in AI-driven smart agriculture.", "এআই-চালিত স্মার্ট কৃষি বিষয়ক একাডেমিক গবেষণার জন্য তৈরি।"),

    # Server (Flask) messages
    "server.no_file": ("No file selected.", "কোনো ফাইল বাছাই করা হয়নি।"),
    "server.unsupported": (
        "Unsupported file type. Please upload a JPG, PNG, HEIC, WEBP, GIF, BMP or TIFF image.",
        "এই ধরনের ফাইল সমর্থিত নয়। JPG, PNG, HEIC, WEBP, GIF, BMP বা TIFF ছবি দিন।",
    ),
    "server.failed": ("Something went wrong while analyzing the image: {error}", "ছবি বিশ্লেষণে সমস্যা হয়েছে: {error}"),

    # JavaScript (static/js/app.js, static/js/image-formats.js)
    "js.analyzing": ("Analyzing…", "বিশ্লেষণ চলছে…"),
    "js.preparing_photo": ("Preparing photo…", "ছবি প্রস্তুত হচ্ছে…"),
    "js.preparing": ("preparing…", "প্রস্তুত হচ্ছে…"),
    "js.choose_photo": ("Please choose a leaf photo first.", "আগে একটি পাতার ছবি বাছাই করুন।"),
    "js.too_big": ("That file is {size}. The limit is {max} MB.", "ফাইলটির আকার {size}। সর্বোচ্চ সীমা {max} MB।"),
    "js.too_big_converted": (
        "After conversion this photo is {size}, over the {max} MB limit. Try a smaller photo or a JPG.",
        "রূপান্তরের পর ছবিটির আকার {size}, যা {max} MB সীমার বেশি। ছোট ছবি বা JPG ব্যবহার করুন।",
    ),
    "js.downloading": ("Downloading the AI model (one time, {mb} MB)…", "এআই মডেল ডাউনলোড হচ্ছে (একবারই, {mb} MB)…"),
    "js.analyzing_leaf": ("Analyzing the leaf…", "পাতাটি বিশ্লেষণ করা হচ্ছে…"),
    "js.offline": (
        "You appear to be offline. Connect to the internet once so the AI model can download.",
        "আপনি অফলাইনে আছেন। এআই মডেল ডাউনলোডের জন্য একবার ইন্টারনেটে সংযুক্ত হন।",
    ),
    "js.failed": (
        "Something went wrong while analyzing the image. Please try again or use a different photo.",
        "ছবি বিশ্লেষণে সমস্যা হয়েছে। আবার চেষ্টা করুন অথবা অন্য একটি ছবি ব্যবহার করুন।",
    ),
    "js.unsupported": (
        "Unsupported file type. Please choose a JPG, PNG, WEBP, HEIC, AVIF, GIF, BMP or TIFF image.",
        "এই ধরনের ফাইল সমর্থিত নয়। JPG, PNG, WEBP, HEIC, AVIF, GIF, BMP বা TIFF ছবি দিন।",
    ),
    "js.convert_offline": (
        "Converting this photo needs an internet connection the first time. Please try again online.",
        "এই ছবিটি রূপান্তরের জন্য প্রথমবার ইন্টারনেট সংযোগ প্রয়োজন। অনলাইনে থেকে আবার চেষ্টা করুন।",
    ),
    "js.convert_failed": (
        "This photo could not be converted. Try exporting it as JPG or PNG.",
        "ছবিটি রূপান্তর করা যায়নি। JPG বা PNG হিসেবে সেভ করে আবার চেষ্টা করুন।",
    ),
    "js.unreadable": (
        "This image could not be read. Try a JPG or PNG photo instead.",
        "ছবিটি পড়া যাচ্ছে না। JPG বা PNG ছবি দিয়ে চেষ্টা করুন।",
    ),
    "js.coming_soon": ("{crop} leaf disease detection is coming soon.", "{crop} পাতার রোগ শনাক্তকরণ শীঘ্রই আসছে।"),
}

# Keys the browser scripts need (embedded in every page as JSON)
JS_KEYS = [k for k in STRINGS if k.startswith("js.")] + [
    "nav.open_menu", "nav.close_menu", "upload.analyze", "result.healthy", "result.disease",
    "result.care", "result.actions", "result.confidence_aria", "title.result",
    "crop.Papaya", "crop.Guava", "crop.Tomato",
]

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def normalize_lang(lang):
    return lang if lang in LANGS else DEFAULT_LANG


def num(value, lang):
    """Render digits in the page language (Bangla digits on Bangla pages)."""
    text = str(value)
    return text.translate(BN_DIGITS) if lang == "bn" else text


def translator(lang):
    idx = LANGS.index(normalize_lang(lang))

    def t(key, **kw):
        text = STRINGS[key][idx]
        # crop="papaya" fills both {crop} ("papaya"/"পেঁপে") and {Crop} ("Papaya"/"পেঁপে")
        if kw.get("crop") in ("papaya", "guava", "tomato"):
            code = kw["crop"]
            kw["crop"] = STRINGS[f"crop.{code}"][idx]
            kw["Crop"] = STRINGS[f"crop.{code.capitalize()}"][idx]
        if kw:
            text = text.format(**kw)
        return Markup(text) if key.endswith(".html") else text

    return t


def js_strings(lang):
    idx = LANGS.index(normalize_lang(lang))
    return {k: STRINGS[k][idx] for k in JS_KEYS}


def localized_info(crop, lang, class_names):
    """{class: {name, description, instructions, is_healthy}} in the given language."""
    en = disease_info.DISEASE_INFO if crop == "papaya" else guava_disease_info.DISEASE_INFO
    bn = disease_info_bn.PAPAYA if crop == "papaya" else disease_info_bn.GUAVA
    out = {}
    for name in class_names:
        base = en.get(name, {})
        item = {
            "name": name.replace("_", " "),
            "description": base.get("description", ""),
            "instructions": list(base.get("instructions", [])),
            "is_healthy": bool(base.get("is_healthy", False)),
        }
        if normalize_lang(lang) == "bn" and name in bn:
            item.update({k: bn[name][k] for k in ("name", "description", "instructions")})
        out[name] = item
    return out


def lang_path(path, lang):
    """English path ('/', '/guava') -> path for the given language."""
    if normalize_lang(lang) == "en":
        return path
    return "/bn/" if path == "/" else "/bn" + path


def lang_from_path(path):
    return "bn" if path == "/bn" or path.startswith("/bn/") else "en"


# ---------- Flask integration (used by app.py and tools/build_static.py) ----------

HOME_ENDPOINTS = {"index": "index", "index_bn": "index", "guava_index": "guava_index", "guava_index_bn": "guava_index"}


def request_lang():
    from flask import request
    if request.method == "POST":
        return normalize_lang(request.form.get("lang"))
    return lang_from_path(request.path)


def flask_context():
    from flask import request, url_for

    lang = request_lang()
    endpoint = request.endpoint or ""
    home = HOME_ENDPOINTS.get(endpoint) or ("guava_index" if endpoint.startswith("guava") else "index")
    en_url = url_for(home)
    return {
        "lang": lang,
        "t": translator(lang),
        "n": lambda value: num(value, lang),
        "lurl": lambda name: lang_path(url_for(name), lang),
        "lang_urls": {"en": en_url, "bn": lang_path(en_url, "bn")},
        "is_home_page": endpoint in HOME_ENDPOINTS,
        "js_i18n": js_strings(lang),
    }


def register(app):
    """Add the Bangla page routes and template helpers to a Flask app that
    already defines the index and guava_index views."""
    app.add_url_rule("/bn/", "index_bn", app.view_functions["index"])
    app.add_url_rule("/bn/guava", "guava_index_bn", app.view_functions["guava_index"])
    app.context_processor(flask_context)
