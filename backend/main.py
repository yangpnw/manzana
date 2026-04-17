import functions_framework
import random
from flask import jsonify

FUN_FACTS = [
    {"headline": "Honey Never Spoils", "narrative": "Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible. Its low moisture and acidic pH create an environment where bacteria cannot survive.", "image": "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400"},
    {"headline": "Bananas are Berries", "narrative": "Botanically speaking, bananas qualify as berries because they grow from a single ovary. Interestingly, strawberries are not true berries because their seeds are on the outside.", "image": "https://images.unsplash.com/photo-1528825871115-3581a5387919?w=400"},
    {"headline": "Wombat Poop is Square", "narrative": "Wombats are the only animals in the world known to produce cube-shaped poop. This unique shape prevents the droppings from rolling away, helping them mark their territory on rocky terrain."},
    {"headline": "Octopuses Have Three Hearts", "narrative": "Two hearts pump blood to the gills, while the third circulates it to the rest of the body. When an octopus swims, the systemic heart actually stops beating, which is why they prefer crawling.", "image": "https://images.unsplash.com/photo-1545671913-b89ac1b4ac10?w=400"},
    {"headline": "Shortest War in History", "narrative": "The Anglo-Zanzibar War of 1896 lasted between 38 and 45 minutes before a ceasefire was called. The British fleet quickly overwhelmed the Sultan's forces, making it the briefest conflict ever recorded."},
    {"headline": "Cow Magnetism", "narrative": "Research using Google Earth images has shown that cattle tend to face either magnetic North or South while grazing or resting. Scientists still don't fully understand the mechanism behind this internal compass."},
    {"headline": "The Eiffel Tower Grows", "narrative": "Due to thermal expansion, the Eiffel Tower can grow by up to 15 centimeters (6 inches) during the summer. The iron heats up, the atoms move more, and the structure physically expands.", "image": "https://images.unsplash.com/photo-1511739001486-6bfe10ce785f?w=400"},
    {"headline": "Trees Talk to Each Other", "narrative": "Trees communicate and share nutrients through an underground network of fungi often called the 'Wood Wide Web.' They can even send distress signals about drought or insect attacks."},
    {"headline": "Venus Rotates Backwards", "narrative": "Venus is the only planet in our solar system that rotates clockwise on its axis. It also rotates so slowly that a single day on Venus lasts longer than a year on Earth."},
    {"headline": "Otters Hold Hands", "narrative": "Sea otters often hold hands while sleeping to keep from drifting apart in the water. They sometimes also use kelp to anchor themselves to the ocean floor.", "image": "https://images.unsplash.com/photo-1615966650071-855b15f29ad1?w=400"},
    {"headline": "Turritopsis Dohrnii", "narrative": "Known as the 'immortal jellyfish,' this species can revert its cells back to their earliest form and start its life cycle over again when faced with physical damage or starvation."},
    {"headline": "Scotland's National Animal", "narrative": "The national animal of Scotland is the Unicorn. It was chosen because of its association with purity, innocence, and being a proud, untamable creature in Celtic mythology."},
    {"headline": "Human DNA and Bananas", "narrative": "Humans share about 50% of their DNA with bananas. While we are clearly very different organisms, the basic cellular functions required for life are remarkably similar across species."},
    {"headline": "Cleopatra Lived Closer to iPhones", "narrative": "Cleopatra lived closer in time to the launch of the iPhone than she did to the completion of the Great Pyramid of Giza. The pyramids were already ancient history during her reign."},
    {"headline": "Saturn Rains Diamonds", "narrative": "Extreme pressure on Saturn and Jupiter can turn atmospheric carbon into soot, which then hardens into graphite and eventually diamonds as it falls through the atmosphere."},
    {"headline": "A Cloud Weighs a Million Pounds", "narrative": "The average cumulus cloud weighs roughly 1.1 million pounds. It stays afloat because the air beneath it is even denser and the water droplets are spread across a vast space."},
    {"headline": "Sharks Are Older Than Trees", "narrative": "Sharks have existed for over 400 million years, while the earliest trees appeared about 350 million years ago. Sharks have survived four out of the five big mass extinctions."},
    {"headline": "The Coldest Place in the Universe", "narrative": "The Boomerang Nebula is the coldest known natural place in the universe, with a temperature of -272°C (-458°F), just one degree above absolute zero."},
    {"headline": "Mantises Have One Ear", "narrative": "Praying mantises have a single ear located in the center of their chest. It is specifically tuned to detect the ultrasonic frequencies used by bats to hunt them."},
    {"headline": "Flamingos Are Pink Because of Shrimp", "narrative": "Flamingos are born grey. Their vibrant pink color comes from the carotenoid pigments in the algae and brine shrimp they eat.", "image": "https://images.unsplash.com/photo-1510673398445-94f476ef2cbc?w=400"}
]

@functions_framework.http
def get_fun_facts(request):
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {'Access-Control-Allow-Origin': '*'}
    selection = random.sample(FUN_FACTS, 10)
    return (jsonify(selection), 200, headers)
