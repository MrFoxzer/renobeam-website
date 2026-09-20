#!/usr/bin/env python3
"""RenoBeam programmatic-SEO location page generator.

Generates:
  locations/<state-slug>.html          (50 state pages)
  locations/<city-slug>-<st>.html      (25 city pages)
  locations/index.html                 (hub)
  sitemap.xml                          (root)
  robots.txt                           (root)

Every page is built from data + rotating template variants selected
deterministically by hashing the location name, so pages are unique,
regenerable, and never read identically. No existing site file is touched.

Run:  python3 tools/generate_locations.py
"""

import hashlib
import json
import os
import re

SITE = "https://renobeam.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "locations")
TODAY = "2026-08-26"
OG_IMAGE = SITE + "/images/og-default.png"

# Blog post slugs (pages live in blog/, authored by hand — listed here so the
# sitemap stays regenerable from this one script).
BLOG_POSTS = [
    "how-to-estimate-renovation-jobs-from-photos",
    "why-slow-quotes-lose-remodeling-jobs",
    "contractor-estimating-spreadsheets-vs-takeoff-software-vs-ai",
]

# ---------------------------------------------------------------------------
# DATA — 50 states
# name, abbr, cities (real major cities), neighbors (4 nearby states),
# climate (honest regional conditions), stock (honest housing-stock character)
# ---------------------------------------------------------------------------

STATES = [
    {"name": "Alabama", "abbr": "AL", "cities": ["Birmingham", "Huntsville", "Montgomery", "Mobile", "Tuscaloosa"],
     "neighbors": ["Tennessee", "Georgia", "Florida", "Mississippi"],
     "climate": "long humid summers, heavy spring storms, and hurricane exposure along the Gulf",
     "stock": "brick ranches, mill-town cottages, and fast-growing suburbs around Huntsville and Birmingham"},
    {"name": "Alaska", "abbr": "AK", "cities": ["Anchorage", "Fairbanks", "Juneau", "Wasilla"],
     "neighbors": ["Washington", "Oregon", "California", "Hawaii"],
     "climate": "extreme cold, a short building season, and freight costs that shape every bid",
     "stock": "homes built for serious winters, where materials often arrive by barge or plane"},
    {"name": "Arizona", "abbr": "AZ", "cities": ["Phoenix", "Tucson", "Mesa", "Scottsdale", "Flagstaff"],
     "neighbors": ["California", "Nevada", "Utah", "New Mexico"],
     "climate": "relentless sun, monsoon storms, and desert heat that punishes roofs and exteriors",
     "stock": "stucco-and-tile tract homes, mid-century block ranches, and huge retiree and rental communities"},
    {"name": "Arkansas", "abbr": "AR", "cities": ["Little Rock", "Fayetteville", "Fort Smith", "Bentonville"],
     "neighbors": ["Missouri", "Tennessee", "Mississippi", "Louisiana"],
     "climate": "humid summers, tornado season, and hard storm fronts",
     "stock": "ranch homes, farmhouses, and the fast-growing Northwest Arkansas corridor"},
    {"name": "California", "abbr": "CA", "cities": ["Los Angeles", "San Diego", "San Francisco", "Sacramento", "Fresno"],
     "neighbors": ["Oregon", "Nevada", "Arizona", "Washington"],
     "climate": "seismic requirements, wildfire zones, and coastal moisture",
     "stock": "everything from 1920s bungalows to hillside customs, ADU conversions, and dense multifamily"},
    {"name": "Colorado", "abbr": "CO", "cities": ["Denver", "Colorado Springs", "Aurora", "Fort Collins", "Boulder"],
     "neighbors": ["Wyoming", "Utah", "Kansas", "New Mexico"],
     "climate": "hail seasons, intense UV at altitude, and hard freeze-thaw swings",
     "stock": "older Denver brick, Front Range suburbs, and mountain builds with real snow loads"},
    {"name": "Connecticut", "abbr": "CT", "cities": ["Hartford", "New Haven", "Stamford", "Bridgeport"],
     "neighbors": ["New York", "Massachusetts", "Rhode Island", "New Jersey"],
     "climate": "New England winters and salt air along Long Island Sound",
     "stock": "colonials, capes, and older coastal homes that hide surprises behind every wall"},
    {"name": "Delaware", "abbr": "DE", "cities": ["Wilmington", "Dover", "Newark", "Rehoboth Beach"],
     "neighbors": ["Maryland", "Pennsylvania", "New Jersey", "Virginia"],
     "climate": "coastal humidity and Atlantic storm exposure",
     "stock": "beach-town cottages, brick colonials, and fast-growing Sussex County construction"},
    {"name": "Florida", "abbr": "FL", "cities": ["Miami", "Tampa", "Orlando", "Jacksonville", "Fort Lauderdale"],
     "neighbors": ["Georgia", "Alabama", "South Carolina", "Mississippi"],
     "climate": "hurricanes, wind-load codes, humidity, and salt air",
     "stock": "concrete-block homes, high-rise condos, and some of the largest rental communities in the country"},
    {"name": "Georgia", "abbr": "GA", "cities": ["Atlanta", "Savannah", "Augusta", "Columbus", "Macon"],
     "neighbors": ["Florida", "Alabama", "Tennessee", "South Carolina"],
     "climate": "heat, humidity, and heavy summer storms",
     "stock": "brick ranches, historic in-town neighborhoods, and relentless new-build suburbs around Atlanta"},
    {"name": "Hawaii", "abbr": "HI", "cities": ["Honolulu", "Hilo", "Kailua", "Kahului"],
     "neighbors": ["California", "Washington", "Oregon", "Nevada"],
     "climate": "salt air, tropical moisture, and some of the highest material costs in the country",
     "stock": "single-wall construction, plantation-era homes, and condo towers"},
    {"name": "Idaho", "abbr": "ID", "cities": ["Boise", "Meridian", "Idaho Falls", "Coeur d'Alene"],
     "neighbors": ["Washington", "Oregon", "Montana", "Utah"],
     "climate": "cold winters, dry summers, and one of the fastest-growing markets in the West",
     "stock": "new subdivisions around Boise alongside older farm and mountain properties"},
    {"name": "Illinois", "abbr": "IL", "cities": ["Chicago", "Aurora", "Naperville", "Springfield", "Rockford"],
     "neighbors": ["Wisconsin", "Indiana", "Missouri", "Iowa"],
     "climate": "freeze-thaw winters and lake-effect weather",
     "stock": "Chicago brick two-flats and bungalow-belt homes plus downstate ranches and farmhouses"},
    {"name": "Indiana", "abbr": "IN", "cities": ["Indianapolis", "Fort Wayne", "Evansville", "South Bend", "Carmel"],
     "neighbors": ["Illinois", "Ohio", "Michigan", "Kentucky"],
     "climate": "humid summers and real Midwest winters",
     "stock": "affordable older stock, brick ranches, and steady suburban building around Indianapolis"},
    {"name": "Iowa", "abbr": "IA", "cities": ["Des Moines", "Cedar Rapids", "Davenport", "Iowa City"],
     "neighbors": ["Minnesota", "Illinois", "Nebraska", "Missouri"],
     "climate": "hard winters, derechos, and hail",
     "stock": "farmhouses, post-war ranches, and solid small-town main streets"},
    {"name": "Kansas", "abbr": "KS", "cities": ["Wichita", "Overland Park", "Kansas City", "Topeka"],
     "neighbors": ["Nebraska", "Missouri", "Oklahoma", "Colorado"],
     "climate": "hail country and big seasonal temperature swings",
     "stock": "post-war ranches and fast-growing Johnson County suburbs"},
    {"name": "Kentucky", "abbr": "KY", "cities": ["Louisville", "Lexington", "Bowling Green", "Owensboro"],
     "neighbors": ["Indiana", "Ohio", "Tennessee", "West Virginia"],
     "climate": "humidity and storm fronts rolling through the Ohio Valley",
     "stock": "shotgun houses, brick ranches, and horse-country properties"},
    {"name": "Louisiana", "abbr": "LA", "cities": ["New Orleans", "Baton Rouge", "Shreveport", "Lafayette"],
     "neighbors": ["Texas", "Arkansas", "Mississippi", "Alabama"],
     "climate": "humidity, flood zones, and hurricane exposure",
     "stock": "raised cottages, shotguns, and slab-on-grade suburbs"},
    {"name": "Maine", "abbr": "ME", "cities": ["Portland", "Bangor", "Augusta", "Lewiston"],
     "neighbors": ["New Hampshire", "Vermont", "Massachusetts", "Connecticut"],
     "climate": "long, hard winters and coastal salt air",
     "stock": "capes, farmhouses, and older homes that always hide surprises in the walls"},
    {"name": "Maryland", "abbr": "MD", "cities": ["Baltimore", "Columbia", "Annapolis", "Frederick", "Rockville"],
     "neighbors": ["Virginia", "Pennsylvania", "Delaware", "West Virginia"],
     "climate": "humid summers and coastal storms on the Chesapeake",
     "stock": "Baltimore rowhomes, DC-metro suburbs, and waterfront properties"},
    {"name": "Massachusetts", "abbr": "MA", "cities": ["Boston", "Worcester", "Springfield", "Cambridge", "Lowell"],
     "neighbors": ["New Hampshire", "Connecticut", "Rhode Island", "New York"],
     "climate": "harsh winters and centuries-old housing stock",
     "stock": "triple-deckers, colonials, and capes where nothing is square"},
    {"name": "Michigan", "abbr": "MI", "cities": ["Detroit", "Grand Rapids", "Ann Arbor", "Lansing", "Traverse City"],
     "neighbors": ["Ohio", "Indiana", "Wisconsin", "Illinois"],
     "climate": "lake-effect snow and punishing freeze-thaw cycles",
     "stock": "Detroit brick, up-north cottages, and post-war suburbs"},
    {"name": "Minnesota", "abbr": "MN", "cities": ["Minneapolis", "St. Paul", "St. Cloud", "Rochester", "Duluth"],
     "neighbors": ["Wisconsin", "Iowa", "North Dakota", "South Dakota"],
     "climate": "some of the hardest freeze-thaw cycles in the country",
     "stock": "pre-war farmhouses, mid-century ramblers, lake homes, and a deep rental base in the Twin Cities"},
    {"name": "Mississippi", "abbr": "MS", "cities": ["Jackson", "Gulfport", "Hattiesburg", "Biloxi"],
     "neighbors": ["Louisiana", "Arkansas", "Tennessee", "Alabama"],
     "climate": "Gulf humidity and hurricane exposure",
     "stock": "brick ranches, coastal cottages, and hard-working rural properties"},
    {"name": "Missouri", "abbr": "MO", "cities": ["Kansas City", "St. Louis", "Springfield", "Columbia"],
     "neighbors": ["Illinois", "Kansas", "Iowa", "Arkansas"],
     "climate": "hail, humidity, and hard seasonal swings",
     "stock": "brick bungalows in the cities, ranches everywhere else, and busy investor markets on both sides of the state"},
    {"name": "Montana", "abbr": "MT", "cities": ["Billings", "Missoula", "Bozeman", "Great Falls", "Helena"],
     "neighbors": ["North Dakota", "South Dakota", "Wyoming", "Idaho"],
     "climate": "long winters, wind, and remote job sites",
     "stock": "ranch properties, log builds, and fast-growing Bozeman-area construction"},
    {"name": "Nebraska", "abbr": "NE", "cities": ["Omaha", "Lincoln", "Grand Island", "Kearney"],
     "neighbors": ["South Dakota", "Iowa", "Kansas", "Colorado"],
     "climate": "hail alley and hard winters",
     "stock": "post-war ranches and steady Omaha and Lincoln suburbs"},
    {"name": "Nevada", "abbr": "NV", "cities": ["Las Vegas", "Henderson", "Reno", "Sparks"],
     "neighbors": ["California", "Arizona", "Utah", "Oregon"],
     "climate": "desert heat and one of the most turnover-heavy rental markets anywhere",
     "stock": "stucco tract homes, HOA communities, and high-volume rental portfolios"},
    {"name": "New Hampshire", "abbr": "NH", "cities": ["Manchester", "Nashua", "Concord", "Portsmouth"],
     "neighbors": ["Maine", "Vermont", "Massachusetts", "Rhode Island"],
     "climate": "granite-state winters and short exterior seasons",
     "stock": "capes, colonials, and lake and mountain properties"},
    {"name": "New Jersey", "abbr": "NJ", "cities": ["Newark", "Jersey City", "Trenton", "Atlantic City", "Paterson"],
     "neighbors": ["New York", "Pennsylvania", "Delaware", "Connecticut"],
     "climate": "coastal storms and dense, older suburbs",
     "stock": "capes, split-levels, two-family rentals, and shore homes"},
    {"name": "New Mexico", "abbr": "NM", "cities": ["Albuquerque", "Santa Fe", "Las Cruces", "Rio Rancho"],
     "neighbors": ["Arizona", "Colorado", "Texas", "Oklahoma"],
     "climate": "high-desert sun and monsoon seasons",
     "stock": "adobe and pueblo-style homes with flat roofs that demand real attention"},
    {"name": "New York", "abbr": "NY", "cities": ["New York", "Buffalo", "Rochester", "Syracuse", "Albany"],
     "neighbors": ["New Jersey", "Pennsylvania", "Connecticut", "Massachusetts"],
     "climate": "everything from lake-effect snow upstate to dense urban logistics downstate",
     "stock": "brownstones, co-ops, upstate Victorians, and two-family rentals"},
    {"name": "North Carolina", "abbr": "NC", "cities": ["Charlotte", "Raleigh", "Durham", "Greensboro", "Asheville"],
     "neighbors": ["Virginia", "South Carolina", "Georgia", "Tennessee"],
     "climate": "humidity, coastal hurricanes, and rapid metro growth",
     "stock": "new-build suburbs, mill houses, and brick ranches"},
    {"name": "North Dakota", "abbr": "ND", "cities": ["Fargo", "Bismarck", "Grand Forks", "Minot", "West Fargo"],
     "neighbors": ["Minnesota", "South Dakota", "Montana", "Wyoming"],
     "climate": "brutal winters and a short, intense building season",
     "stock": "farmsteads, solid small-town homes, and fast-built Fargo-area apartments and suburbs"},
    {"name": "Ohio", "abbr": "OH", "cities": ["Columbus", "Cleveland", "Cincinnati", "Dayton", "Toledo"],
     "neighbors": ["Michigan", "Indiana", "Pennsylvania", "Kentucky"],
     "climate": "freeze-thaw winters and lake-effect snow off Erie",
     "stock": "century homes, brick colonials, and some of the most affordable rental stock in the Midwest"},
    {"name": "Oklahoma", "abbr": "OK", "cities": ["Oklahoma City", "Tulsa", "Norman", "Broken Arrow"],
     "neighbors": ["Texas", "Kansas", "Arkansas", "Missouri"],
     "climate": "hail, tornado season, and big temperature swings",
     "stock": "post-war ranches and growing OKC and Tulsa suburbs"},
    {"name": "Oregon", "abbr": "OR", "cities": ["Portland", "Salem", "Eugene", "Bend", "Medford"],
     "neighbors": ["Washington", "California", "Idaho", "Nevada"],
     "climate": "constant moisture west of the Cascades and wildfire country east of them",
     "stock": "craftsman bungalows, mid-century ranches, and rural properties"},
    {"name": "Pennsylvania", "abbr": "PA", "cities": ["Philadelphia", "Pittsburgh", "Allentown", "Erie", "Harrisburg"],
     "neighbors": ["New York", "New Jersey", "Ohio", "Maryland"],
     "climate": "real winters and some of the oldest housing stock in America",
     "stock": "rowhomes, stone farmhouses, and coal-region doubles"},
    {"name": "Rhode Island", "abbr": "RI", "cities": ["Providence", "Warwick", "Cranston", "Newport"],
     "neighbors": ["Massachusetts", "Connecticut", "New York", "New Hampshire"],
     "climate": "coastal New England weather",
     "stock": "triple-deckers, capes, and shoreline cottages"},
    {"name": "South Carolina", "abbr": "SC", "cities": ["Charleston", "Columbia", "Greenville", "Myrtle Beach"],
     "neighbors": ["North Carolina", "Georgia", "Florida", "Tennessee"],
     "climate": "coastal humidity, hurricane exposure, and a booming coastal market",
     "stock": "Lowcountry homes, brick ranches, and fast-growing beach-town construction"},
    {"name": "South Dakota", "abbr": "SD", "cities": ["Sioux Falls", "Rapid City", "Aberdeen", "Brookings"],
     "neighbors": ["North Dakota", "Minnesota", "Nebraska", "Montana"],
     "climate": "hard winters and hail",
     "stock": "farm properties and steady Sioux Falls growth"},
    {"name": "Tennessee", "abbr": "TN", "cities": ["Nashville", "Memphis", "Knoxville", "Chattanooga", "Franklin"],
     "neighbors": ["Kentucky", "Virginia", "North Carolina", "Georgia"],
     "climate": "humidity, storm fronts, and some of the fastest metro growth in the Southeast",
     "stock": "brick ranches, new tall-skinny infill, and deep investor activity in Memphis and Nashville"},
    {"name": "Texas", "abbr": "TX", "cities": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth"],
     "neighbors": ["Oklahoma", "New Mexico", "Arkansas", "Louisiana"],
     "climate": "hail, coastal hurricanes, foundation-moving clay soils, and punishing heat",
     "stock": "slab-on-grade suburbs, ranch homes, and some of the largest rental portfolios in the country"},
    {"name": "Utah", "abbr": "UT", "cities": ["Salt Lake City", "Provo", "Ogden", "St. George", "Lehi"],
     "neighbors": ["Idaho", "Wyoming", "Colorado", "Nevada"],
     "climate": "snow loads, high-desert sun, and one of the youngest, fastest-building markets in the country",
     "stock": "new Wasatch Front suburbs and older Salt Lake bungalows"},
    {"name": "Vermont", "abbr": "VT", "cities": ["Burlington", "Montpelier", "Rutland", "Stowe"],
     "neighbors": ["New Hampshire", "New York", "Massachusetts", "Maine"],
     "climate": "long winters and old bones",
     "stock": "farmhouses, capes, and village homes that predate modern framing"},
    {"name": "Virginia", "abbr": "VA", "cities": ["Virginia Beach", "Richmond", "Norfolk", "Arlington", "Charlottesville"],
     "neighbors": ["Maryland", "North Carolina", "Tennessee", "West Virginia"],
     "climate": "humid summers and coastal storm exposure",
     "stock": "colonials, DC-metro suburbs, and historic in-town homes"},
    {"name": "Washington", "abbr": "WA", "cities": ["Seattle", "Spokane", "Tacoma", "Vancouver", "Bellevue"],
     "neighbors": ["Oregon", "Idaho", "Montana", "California"],
     "climate": "constant moisture west of the Cascades",
     "stock": "craftsman homes, mid-century ranches, and dense Puget Sound multifamily"},
    {"name": "West Virginia", "abbr": "WV", "cities": ["Charleston", "Huntington", "Morgantown", "Wheeling"],
     "neighbors": ["Virginia", "Maryland", "Pennsylvania", "Ohio"],
     "climate": "mountain weather and challenging terrain",
     "stock": "older frame homes and hollow-to-hollow rural properties"},
    {"name": "Wisconsin", "abbr": "WI", "cities": ["Milwaukee", "Madison", "Green Bay", "Kenosha", "Eau Claire"],
     "neighbors": ["Minnesota", "Iowa", "Illinois", "Michigan"],
     "climate": "hard freeze-thaw winters and lake-effect weather",
     "stock": "cream-city brick, farmhouses, northwoods cottages, and Milwaukee duplexes"},
    {"name": "Wyoming", "abbr": "WY", "cities": ["Cheyenne", "Casper", "Jackson", "Laramie"],
     "neighbors": ["Montana", "Colorado", "Utah", "Nebraska"],
     "climate": "wind, snow loads, and remote sites",
     "stock": "ranch properties and mountain builds"},
]

# ---------------------------------------------------------------------------
# DATA — 25 major rental-market cities
# hoods: real, well-known neighborhoods/areas; color: honest market character
# ---------------------------------------------------------------------------

CITIES = [
    {"name": "Minneapolis", "abbr": "MN", "state": "Minnesota",
     "hoods": ["Uptown", "Northeast", "Linden Hills", "Longfellow", "North Loop"],
     "color": "a housing stock heavy on 1900s-1920s craftsman bungalows and story-and-a-halfs, plus one of the Midwest's most active rental markets"},
    {"name": "St. Paul", "abbr": "MN", "state": "Minnesota",
     "hoods": ["Highland Park", "Summit Hill", "Mac-Groveland", "Como Park", "Cathedral Hill"],
     "color": "Victorian and craftsman stock that runs even older than Minneapolis in places, with duplexes and small multifamily on block after block"},
    {"name": "St. Cloud", "abbr": "MN", "state": "Minnesota",
     "hoods": ["Pantown", "downtown St. Cloud", "Waite Park", "Sartell", "Sauk Rapids"],
     "color": "granite-city stock that runs from pre-war homes near the Mississippi to new builds pushing toward Sartell, plus steady student-rental turnover around SCSU"},
    {"name": "Rochester", "abbr": "MN", "state": "Minnesota",
     "hoods": ["downtown Rochester", "Kutzky Park", "Slatterly Park", "Pill Hill", "Country Club Manor"],
     "color": "a market anchored by the Mayo Clinic — steady relocation demand, a deep rental base, and homes that turn over on a schedule"},
    {"name": "Fargo", "abbr": "ND", "state": "North Dakota",
     "hoods": ["downtown Fargo", "Hawthorne", "Horace Mann", "West Fargo", "Moorhead"],
     "color": "a short, intense building season and one of the upper Midwest's fastest-growing apartment markets"},
    {"name": "Chicago", "abbr": "IL", "state": "Illinois",
     "hoods": ["Lincoln Park", "Logan Square", "Wicker Park", "Hyde Park", "Pilsen"],
     "color": "brick two-flats, greystones, and bungalow-belt stock that demands masonry-aware pricing"},
    {"name": "New York", "abbr": "NY", "state": "New York",
     "hoods": ["Park Slope", "Astoria", "Bed-Stuy", "the Upper West Side", "Riverdale"],
     "color": "co-ops, brownstones, and walk-ups where logistics — freight elevators, board approvals, alternate-side parking — are half the job"},
    {"name": "Los Angeles", "abbr": "CA", "state": "California",
     "hoods": ["Silver Lake", "Highland Park", "Venice", "Sherman Oaks", "Echo Park"],
     "color": "1920s Spanish bungalows, hillside customs, seismic retrofits, and ADU conversions on seemingly every block"},
    {"name": "Houston", "abbr": "TX", "state": "Texas",
     "hoods": ["The Heights", "Montrose", "EaDo", "Katy", "Sugar Land"],
     "color": "no-zoning sprawl, slab-on-grade stock, flood-recovery work, and clay soils that keep foundation crews busy"},
    {"name": "Dallas", "abbr": "TX", "state": "Texas",
     "hoods": ["Oak Cliff", "Lakewood", "Bishop Arts District", "Preston Hollow", "Frisco"],
     "color": "expansive clay soils, hail seasons, and everything from Preston Hollow customs to huge single-family rental portfolios"},
    {"name": "Austin", "abbr": "TX", "state": "Texas",
     "hoods": ["East Austin", "Hyde Park", "Zilker", "Mueller", "South Congress"],
     "color": "tear-down-and-rebuild infill, 1950s ranches getting opened up, and a construction market that has run hot for a decade"},
    {"name": "San Antonio", "abbr": "TX", "state": "Texas",
     "hoods": ["Alamo Heights", "Monte Vista", "Southtown", "Stone Oak", "Terrell Hills"],
     "color": "historic stock in Monte Vista and Southtown alongside fast-growing north-side suburbs, at price points well below Austin"},
    {"name": "Phoenix", "abbr": "AZ", "state": "Arizona",
     "hoods": ["Arcadia", "Ahwatukee", "Roosevelt Row", "North Phoenix", "Desert Ridge"],
     "color": "stucco and tile, block-wall yards, sun-beaten exteriors, and one of the biggest single-family rental markets in America"},
    {"name": "Denver", "abbr": "CO", "state": "Colorado",
     "hoods": ["Wash Park", "LoHi", "Park Hill", "Capitol Hill", "Berkeley"],
     "color": "hail claims, pop-tops on brick bungalows, and a metro that runs from Victorian blocks to brand-new suburbs"},
    {"name": "Seattle", "abbr": "WA", "state": "Washington",
     "hoods": ["Ballard", "Capitol Hill", "West Seattle", "Queen Anne", "Fremont"],
     "color": "craftsman remodels, year-round moisture management, backyard DADUs, and some of the highest labor rates in the country"},
    {"name": "Atlanta", "abbr": "GA", "state": "Georgia",
     "hoods": ["Grant Park", "Inman Park", "Old Fourth Ward", "Decatur", "Buckhead"],
     "color": "in-town bungalow renovations alongside one of the country's largest build-to-rent and investor footprints"},
    {"name": "Miami", "abbr": "FL", "state": "Florida",
     "hoods": ["Coral Gables", "Wynwood", "Little Havana", "Coconut Grove", "Brickell"],
     "color": "condo-board work, impact windows, salt-air corrosion, and recertification-driven renovation demand across older buildings"},
    {"name": "Tampa", "abbr": "FL", "state": "Florida",
     "hoods": ["Seminole Heights", "Hyde Park", "Ybor City", "Westchase", "Brandon"],
     "color": "bungalows in Seminole Heights, block ranches, flood-zone questions, and hurricane-driven repair cycles"},
    {"name": "Orlando", "abbr": "FL", "state": "Florida",
     "hoods": ["Winter Park", "College Park", "Thornton Park", "Lake Nona", "Kissimmee"],
     "color": "vacation-rental refreshes near the parks, HOA communities, and block-home renovations from College Park to Kissimmee"},
    {"name": "Charlotte", "abbr": "NC", "state": "North Carolina",
     "hoods": ["NoDa", "Plaza Midwood", "Dilworth", "South End", "Ballantyne"],
     "color": "one of the Southeast's fastest-growing metros — mill-house renovations in NoDa and Plaza Midwood plus relentless suburban building"},
    {"name": "Nashville", "abbr": "TN", "state": "Tennessee",
     "hoods": ["East Nashville", "The Nations", "Germantown", "12South", "Sylvan Park"],
     "color": "tall-skinny infill, East Nashville flips, and short-term-rental renovations in a metro that keeps adding cranes"},
    {"name": "Las Vegas", "abbr": "NV", "state": "Nevada",
     "hoods": ["Summerlin", "Henderson", "Green Valley", "Spring Valley", "the Arts District"],
     "color": "stucco tract homes, HOA repaints, and rental turnover at a scale few markets can match"},
    {"name": "Columbus", "abbr": "OH", "state": "Ohio",
     "hoods": ["Short North", "German Village", "Clintonville", "Grandview Heights", "Westerville"],
     "color": "century homes in German Village, student rentals near Ohio State, and one of the Midwest's steadiest growth markets"},
    {"name": "Indianapolis", "abbr": "IN", "state": "Indiana",
     "hoods": ["Broad Ripple", "Fountain Square", "Irvington", "Meridian-Kessler", "Herron-Morton"],
     "color": "one of the country's biggest single-family rental investor markets, with affordable stock from Fountain Square to Irvington"},
    {"name": "Kansas City", "abbr": "MO", "state": "Missouri",
     "hoods": ["Brookside", "Waldo", "Westport", "River Market", "the Crossroads"],
     "color": "shirtwaist houses, post-war ranches, hail seasons, and an investor market that spans both sides of the state line"},
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def slugify(text):
    s = text.lower().replace("'", "").replace(".", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def state_slug(name):
    return slugify(name)


def city_slug(city):
    return slugify(city["name"]) + "-" + city["abbr"].lower()


def hnum(name, salt):
    return int(hashlib.md5((name + "|" + str(salt)).encode()).hexdigest(), 16)


def pick(name, salt, options):
    return options[hnum(name, salt) % len(options)]


# Words whose written first letter is a vowel but whose SOUND is a consonant
# (or vice versa). "Utah" begins with the consonant glide /j/ -> "a Utah".
_A_BEFORE_VOWEL_LETTER = {"utah", "european", "one", "once", "uniform", "unit", "user"}
_AN_BEFORE_CONSONANT_LETTER = {"hour", "honest", "honor", "heir"}


def article(word, cap=False):
    """Return 'a' or 'an' for `word`, chosen by its initial SOUND."""
    first = word.strip().split()[0].lower().strip("\"'([")
    if first in _A_BEFORE_VOWEL_LETTER:
        a = "a"
    elif first in _AN_BEFORE_CONSONANT_LETTER:
        a = "an"
    elif first[:1] in "aeiou":
        a = "an"
    else:
        a = "a"
    return a.capitalize() if cap else a


def oxford(items):
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return items[0] + " and " + items[1]
    return ", ".join(items[:-1]) + ", and " + items[-1]


# ---------------------------------------------------------------------------
# Copy variants — every section has 4+ rotating variants
# ---------------------------------------------------------------------------

H1S = [
    'Renovation estimating software in <span class="grad-text">{loc}</span>',
    'AI renovation estimates for <span class="grad-text">{loc}</span> contractors',
    'Renovation estimating software built for <span class="grad-text">{loc}</span>',
    'Price renovation work in <span class="grad-text">{loc}</span> in minutes',
]

METAS = [
    "AI renovation estimating software for {loc} contractors. Photos and a walkthrough video in — line-item labor, materials, and {loc}-adjusted pricing out. In development.",
    "Quote renovation work in {loc} in minutes. RenoBeam will turn phone photos into line-item estimates with regional pricing and branded PDF proposals. Pre-launch.",
    "Renovation estimating software planned for the {loc} market. Line-item labor and materials, regional price adjustment, client-ready PDFs. Join the early-access list.",
    "Built by a working contractor: RenoBeam will turn {art} {loc} walkthrough video into an itemized renovation estimate with local pricing and a branded proposal PDF.",
]

INTRO_A = [
    "RenoBeam will turn a phone walkthrough into a line-item renovation estimate priced for {loc}. Upload photos and a short video of any space, and you get labor, materials, and quantities back in minutes — adjusted to {market} pricing — plus a branded, client-ready PDF proposal.",
    "Upload photos and a short walkthrough video of any space in {loc}, and RenoBeam will return a full line-item estimate — labor, materials, and quantities, adjusted to {market} pricing — plus a branded PDF proposal you can send the same day. That is the product we are building — it is not open yet.",
    "In {loc}, the contractor who quotes first usually wins the job. RenoBeam is being built to turn phone photos and a short walkthrough video into a line-item estimate — labor, materials, quantities, {market} pricing — and a branded PDF proposal, in minutes.",
    "Estimating eats evenings. RenoBeam is being built to give them back to {loc} contractors: photos and a short walkthrough video go in, and a line-item estimate — labor, materials, quantities, priced for the {market2} — comes out, with a client-ready branded PDF attached.",
    "RenoBeam is an AI renovation estimator in development, built by a working remodeling contractor — and built to price work the way {loc} contractors actually bid it. Photos and a short video in; itemized labor, materials, and {market} pricing out, with a branded PDF proposal ready to send.",
]

INTRO_B = [
    "Remodeling contractors, general contractors, kitchen and bath specialists, handyman services, roofing and painting pros — if you price work anywhere in {loc}, RenoBeam hands you a defensible estimate before you leave the driveway.",
    "It's built for anyone quoting work in {loc}: remodelers, GCs, kitchen and bath crews, handyman services, roofers, and painting contractors who would rather be building than typing up bids at 10 p.m.",
    "Whether you run a remodeling company, a GC operation, a kitchen and bath shop, a handyman service, or a roofing or painting crew serving {loc}, the goal is the same: quote faster than the competition without guessing at numbers.",
    "If your trucks run anywhere in {loc} — remodeling, general contracting, kitchen and bath, handyman work, roofing, painting — RenoBeam is the estimator in your pocket, built by someone who prices jobs for a living.",
]

WHY_HEADS = [
    "Why {loc} contractors quote with RenoBeam",
    "Estimating in {loc} is its own animal",
    "Built for the way {loc} prices work",
    "The {loc} market, priced honestly",
]

WHY_STATE = [
    "<p>{name} renovation work runs the gamut: {stock}. Add {climate}, and pricing a job here means knowing what the local market actually bears — not what a national average says it should. RenoBeam's regional pricing engine adjusts labor and material baselines to your {name} market, whether you're bidding in {c0}, {c1}, or {c2}.</p><p>And because RenoBeam is a cloud product, there will be no office to visit and nothing to install. It is designed to work wherever you and your phone do — {clist}, and every town between them: capture the space on site, and the estimate is waiting before you're back at the truck.</p>",
    "<p>From {c0} to {c1} to {c2}, {name} contractors deal with {stock} — and with {climate}. That mix punishes lazy estimates. A bid that ignores what {name} labor and materials really cost either leaves money on the table or loses the job. RenoBeam adjusts every baseline to your market, then lets you override any line with your own rates.</p><p>There will be no local office to visit, because there doesn't need to be one: at launch, RenoBeam will be available everywhere in {name} the moment you sign up. If your phone gets a signal on the job site — or even if it doesn't until you're back in coverage — your walkthrough becomes an estimate in minutes.</p>",
    "<p>What makes {name} estimating hard isn't the math — it's the variety. The housing stock spans {stock}, the weather brings {climate}, and prices in {c0} don't match prices in {c3}. RenoBeam handles the variety for you: regional price adjustment tunes labor and material baselines to the market you're actually standing in, and your own price book overrides win every time.</p><p>RenoBeam will launch across all of {name} as a cloud product — {clist} and everywhere in between — with nothing to install and no hardware beyond the phone already in your pocket.</p>",
    "<p>Ask anyone bidding work in {c0}, {c1}, or {c2}: {name} jobs come with their own conditions. {climate_cap} shape what gets rebuilt and when, and the stock itself — {stock} — means no two walkthroughs look alike. RenoBeam was built by a working remodeling contractor who prices exactly this kind of variety for a living, and its estimates are structured the way real bids are.</p><p>Because it's cloud software, RenoBeam will cover every corner of {name} from day one. No territory limits, no installs — just capture, upload, and send the proposal.</p>",
]

WHY_CITY = [
    "<p>{name} is not a generic market: {color}. Bidding here means knowing what {name} labor and materials actually run, and RenoBeam's regional pricing engine adjusts every baseline to match — then lets your own price book override any number. From {h0} to {h1} to {h2}, the estimate fits the neighborhood you're standing in.</p><p>RenoBeam is a cloud product, so at launch it will be available everywhere crews work in {full} — no office to visit, nothing to install. Capture the space with your phone, and the line-item estimate is ready before you've pulled away from the curb.</p>",
    "<p>Work in {name} long enough and you learn the market has a personality: {color}. A national-average estimate doesn't survive contact with that reality. RenoBeam prices to the {name} market, itemizes labor and materials with quantities, and turns it all into a branded proposal — whether the job is in {h0}, {h1}, or out toward {h4}.</p><p>And because RenoBeam is cloud software, it will cover every {name} zip code from day one. There's no local franchise and no territory map — just your phone, your walkthrough, and an estimate in minutes.</p>",
    "<p>The {name} renovation scene is defined by {color}. That's exactly the kind of market where itemized, locally priced estimates win: clients here see plenty of bids, and the vague lump-sum quote is the first one in the trash. RenoBeam breaks every job into the line items {name} contractors actually price — from a kitchen in {h0} to a bath in {h2} to a full-gut in {h3}.</p><p>It's a cloud product that will launch across {full} and its suburbs with nothing to install. Walk the space, upload the capture, send the proposal — often before your competitor has booked their site visit.</p>",
    "<p>Every {name} contractor knows the stock: {color}. Pricing that work takes local awareness, and that's what RenoBeam's regional adjustment delivers — labor and material baselines tuned to the {name} market, with your own price book layered on top. Jobs in {h0}, {h1}, {h2}, and {h3} each get priced like the distinct work they are.</p><p>RenoBeam will be available throughout {full} as a cloud product — no office, no hardware, no waiting list by territory. If you can walk the space with a phone, you can bid it the same afternoon.</p>",
]

FEAT_HEADS = [
    "What RenoBeam will do on {art} {loc} job site",
    "Features that earn their keep in {loc}",
    "Built for how {loc} bids get won",
    "The RenoBeam toolkit, put to work in {loc}",
]

# Feature pool: each entry = (title, [3 body variants]). Bodies use {loc}, {pair}, {market2}.
FEATURES = [
    ("Regional price adjustment", [
        "Labor and material baselines tuned to the {market2}, so a bathroom {pair} doesn't get priced like one three states away.",
        "RenoBeam adjusts its pricing baselines to the {market2} — the difference between a bid that wins in {loc} and one that gets laughed out.",
        "Every estimate starts from baselines adjusted to the {market2}, not a national average that fits nowhere.",
    ]),
    ("Photo + video capture", [
        "A handful of photos and a sub-minute walkthrough video from any phone — no laser scanner, no special hardware, no training for the crew.",
        "Any phone camera is enough. Snap each wall, record a short walkthrough, and upload straight from job sites {pair}.",
        "No hardware to buy: photos plus a short video from the phone already in your pocket is all the input RenoBeam needs.",
    ]),
    ("Line items, not lump sums", [
        "Labor, materials, and quantities itemized for every scope — demo, framing, drywall, flooring, paint, electrical — so you can defend every number {art} {loc} client questions.",
        "Estimates arrive broken into the line items real contractors price: labor and materials, separated, with quantities — a bid you can defend in any {loc} living room.",
        "No vague totals. Every scope is itemized with labor, materials, and quantities, structured the way working {loc} contractors actually build a bid.",
    ]),
    ("Branded PDF proposals", [
        "One tap turns the estimate into a polished proposal with your logo and terms — sent before slower {loc} competitors have opened their spreadsheet.",
        "Client-ready PDFs with your branding and terms, generated instantly — the {loc} contractor who quotes first usually wins.",
        "Turn any estimate into a branded, client-ready proposal in one tap and get it in the client's inbox the same day you walked the space.",
    ]),
    ("Your price book", [
        "Override any rate with your real numbers — your subs, your suppliers, your margins — and RenoBeam applies them to every future {loc} estimate.",
        "Your subs and suppliers set your real costs. Feed them in once and every estimate after that prices the way your {loc} business actually prices.",
        "RenoBeam learns your rates: override any line once and your price book carries into every future bid you send in {loc}.",
    ]),
    ("Takeoffs measured for you", [
        "Square footage, linear footage, and unit counts pulled straight from your capture — the takeoff work that normally eats {art} {loc} contractor's evenings.",
        "Quantities come measured from the walkthrough itself: square feet of drywall, linear feet of trim, unit counts — no tape-measure evenings.",
        "The measuring is done for you — areas, lengths, and counts extracted from your photos and video, ready to price.",
    ]),
    ("Built for crews", [
        "Team seats on the Crew plan let a lead carpenter capture a space {pair} and fire off the estimate — without you on site.",
        "With team seats, your PM or lead will be able to walk {art} {loc} job and send the estimate while you're bidding the next one.",
        "Five seats on the Crew plan mean whoever is closest walks the space — and the estimate still goes out under your brand.",
    ]),
    ("API access", [
        "On the Firm plan, pipe every {loc} estimate straight into your CRM, job-management platform, or insurance workflow.",
        "Firm-plan API access connects RenoBeam to the systems a high-volume {loc} operation already runs on.",
        "Estimates don't have to live in another silo: the Firm plan's API feeds them into your existing CRM or claims workflow.",
    ]),
]

PRICE_HEADS = [
    "Planned pricing for {loc} pros",
    "Planned plans, built to pay for themselves on one {loc} bid",
    "Planned pricing, wherever in {loc} you work",
    "The plans we intend to launch with in {loc}",
]

PRICE_INTROS = [
    "These are the three plans RenoBeam intends to launch with, billed monthly in USD. Nothing is for sale yet — join the early-access list and we'll email you when it is.",
    "Planned pricing at launch, billed monthly in USD. There is no checkout on this site today; the waitlist is the only way in right now.",
    "Here is the pricing we plan to open with: volume, seats, and branding, billed monthly in USD. Figures may change before launch.",
    "Planned pricing, in USD per month. No accounts, no checkout, and no card are involved yet — just the early-access list.",
]

CTA_HEADS = [
    'Your next {loc} bid, <span class="grad-text">done in minutes</span>',
    'Quote your next {loc} job <span class="grad-text">before you leave the driveway</span>',
    'Get early access. <span class="grad-text">Zero risk.</span>',
    'Stop typing bids at midnight, <span class="grad-text">{loc}</span>',
]

CTA_BODIES = [
    "Join the early-access list and be first in when RenoBeam opens in {loc}. No account, no card, no charge — just your place in line.",
    "Get on the early-access list today. We'll email you as soon as RenoBeam is live in {loc} — nothing to pay and nothing to install.",
    "Early access is forming now. Sign up, and you'll be among the first to see a walkthrough in {loc} turn into a finished proposal.",
    "Put your name on the list and we'll tell you the moment you can test RenoBeam on real work in {loc}. No card, no strings.",
]

HOW_HEADS = [
    "From {loc} walkthrough to winning bid",
    "Three steps between you and the signed {loc} job",
    "How {art} {loc} estimate will come together",
    "Walk it, beam it, send it — {loc} edition",
]

HOW_STEPS = [
    [("Capture the space", "Walk the room with your phone — photos of each wall plus a short video, under a minute. Upload straight from the {loc} job site."),
     ("The beam does the takeoff", "RenoBeam measures the space, itemizes labor and materials with quantities, and adjusts pricing to the {market2}. Review and tweak any line."),
     ("Send the proposal", "Export a branded, client-ready PDF with your logo and terms — sent before you've left the driveway.")],
    [("Walk it with your phone", "A few photos and a quick walkthrough video are the whole capture. No scanner, no clipboard, no return trip to measure."),
     ("Let RenoBeam price it", "Measurements, quantities, labor, and materials come back itemized and adjusted to the {market2} — every line editable before it ships."),
     ("Win the job", "One tap produces a branded PDF proposal. While competitors schedule their second site visit, your number is already in the client's inbox.")],
    [("Shoot the space", "Photos of each wall and a short video from any phone. If your crew can text, they will be able to capture {art} {loc} job for you."),
     ("Review the line items", "RenoBeam returns labor, materials, and quantities priced for the {market2}. Adjust anything — your price book always wins."),
     ("Fire off the proposal", "A branded, client-ready PDF with your terms goes out the same day. Estimating stops being the bottleneck.")],
    [("Capture on site", "Walk the space once, phone in hand — wall photos plus a sub-minute video. That's the entire input."),
     ("Get the itemized estimate", "Minutes later: labor, materials, and measured quantities, adjusted to the {market2} and structured like a real contractor's bid."),
     ("Send it and move on", "Export the branded PDF, hit send, and drive to the next {loc} appointment. The evening at the desk never happens.")],
]


def how_html(loc, market2, key=None):
    key = key or loc
    art = article(loc)
    head = pick(key, "howhead", HOW_HEADS).format(loc=loc, art=art)
    steps = pick(key, "howsteps", HOW_STEPS)
    cells = []
    for i, (t, b) in enumerate(steps, 1):
        body = b.format(loc=loc, market2=market2, art=art)
        cells.append(f"""          <div class="step" data-reveal>
            <span class="step-num">Step 0{i}</span>
            <h3>{t}</h3>
            <p>{body}</p>
          </div>""")
    cells_html = "\n".join(cells)
    return f"""    <section class="section">
      <div class="container">
        <div class="section-head" data-reveal>
          <span class="eyebrow">How it will work</span>
          <h2>{head}</h2>
        </div>
        <div class="steps" data-reveal-group>
{cells_html}
        </div>
      </div>
    </section>
"""


NEARBY_HEADS = [
    "RenoBeam near {loc}",
    "Also serving the neighbors",
    "Wherever the work takes you",
    "More markets, same beam",
]

# ---------------------------------------------------------------------------
# Shared page chrome
# ---------------------------------------------------------------------------

LOC_CSS = """
    .loc-hero { padding: calc(var(--nav-h) + 64px) 0 8px; }
    .loc-breadcrumb { display: flex; flex-wrap: wrap; gap: 8px; font-size: .8rem; color: var(--text-faint); margin-bottom: 18px; }
    .loc-breadcrumb a { color: var(--text-muted); text-decoration: none; }
    .loc-breadcrumb a:hover { color: var(--text); }
    .loc-breadcrumb .sep { opacity: .5; }
    .loc-hero h1 { font-family: var(--font-display); font-size: clamp(2.1rem, 5vw, 3.2rem); line-height: 1.08; letter-spacing: -.02em; margin: 16px 0 20px; max-width: 820px; }
    .loc-intro p { color: var(--text-muted); max-width: 760px; margin: 0 0 14px; }
    .loc-prose p { color: var(--text-muted); max-width: 780px; margin: 0 0 16px; }
    .loc-chips { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 6px; }
    .loc-chip { display: inline-block; padding: 8px 15px; border: 1px solid var(--border); border-radius: 999px; background: var(--surface); font-size: .85rem; color: var(--text-muted); text-decoration: none; transition: border-color .2s, color .2s, background .2s; }
    .loc-chip:hover { border-color: var(--border-strong); background: var(--surface-strong); color: var(--text); }
    .loc-chip strong { color: var(--text); font-weight: 600; }
    .loc-links h3 { font-family: var(--font-display); font-size: 1.02rem; margin: 26px 0 12px; }
    .loc-hub-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; }
    .loc-hub-card { border: 1px solid var(--border); background: var(--surface); border-radius: var(--radius); padding: 18px; }
    .loc-hub-card h3 { font-family: var(--font-display); font-size: 1rem; margin: 0 0 8px; }
    .loc-hub-card h3 a { text-decoration: none; }
    .loc-hub-card h3 a:hover { color: var(--amber); }
    .loc-hub-card ul { list-style: none; margin: 0; padding: 0; }
    .loc-hub-card li { margin: 4px 0; }
    .loc-hub-card li a { font-size: .86rem; color: var(--text-muted); text-decoration: none; }
    .loc-hub-card li a:hover { color: var(--text); }
"""

FAVICON = ("data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20viewBox='0%200%2064%2064'%3E%3Crect%20width='64'"
           "%20height='64'%20rx='14'%20fill='%230e0e13'/%3E%3Cpath%20d='M12%2030%2032%2015%2052%2030'%20fill='none'%20stroke="
           "'%23f97316'%20stroke-width='5'%20stroke-linecap='round'%20stroke-linejoin='round'/%3E%3Cpath%20d='M12%2048%2052%2024'"
           "%20stroke='%23fbbf24'%20stroke-width='5'%20stroke-linecap='round'/%3E%3C/svg%3E")


ANALYTICS = """  <!-- Analytics: paste your GA4 Measurement ID below to activate. Until then this is a no-op. -->
  <script>window.GA_ID="G-XXXXXXXXXX";if(window.GA_ID&&!/^G-X+$/.test(window.GA_ID)){var s=document.createElement('script');s.async=1;s.src='https://www.googletagmanager.com/gtag/js?id='+window.GA_ID;document.head.appendChild(s);window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config',window.GA_ID);}</script>
"""

# Shared pre-launch disclosure. RenoBeam has no signup, checkout or upload yet;
# every page says so in the same words.
PRELAUNCH_NOTE = ('        <p class="prelaunch-note"><strong>Pre-launch:</strong> RenoBeam is still in '
                  'development. There is no sign-up, checkout, or photo upload yet \u2014 the waitlist is the '
                  'only way in, and everything below describes what we are building. '
                  '<a href="/#waitlist">Join the waitlist</a></p>\n')

SUPPORT_EMAIL = "leads@stylemarking.com"


def logo_svg(grad_id):
    return f"""<svg width="30" height="30" viewBox="0 0 32 32" fill="none" aria-hidden="true">
          <defs>
            <linearGradient id="{grad_id}" x1="0" y1="32" x2="32" y2="0" gradientUnits="userSpaceOnUse">
              <stop offset="0" stop-color="#fbbf24"/>
              <stop offset="1" stop-color="#f97316"/>
            </linearGradient>
          </defs>
          <path d="M5 14.5 16 6l11 8.5V27H5Z" stroke="rgba(245,243,239,0.85)" stroke-width="2" stroke-linejoin="round"/>
          <path d="M7 24.5 25 12" stroke="url(#{grad_id})" stroke-width="2.5" stroke-linecap="round"/>
          <circle cx="25" cy="12" r="2.2" fill="#fbbf24"/>
        </svg>"""


def nav_html():
    return f"""  <a class="skip-link" href="#main">Skip to content</a>

  <!-- Aurora background -->
  <div class="aurora" aria-hidden="true">
    <div class="aurora-blob aurora-blob--a"></div>
    <div class="aurora-blob aurora-blob--b"></div>
    <div class="aurora-blob aurora-blob--c"></div>
  </div>
  <div class="noise-overlay" aria-hidden="true"></div>

  <header class="nav">
    <div class="nav-inner">
      <a class="logo" href="/" aria-label="RenoBeam home">
        {logo_svg("logo-grad")}
        <span>Reno<span class="logo-beam-word">Beam</span></span>
      </a>

      <button class="nav-toggle" aria-expanded="false" aria-controls="nav-links" aria-label="Toggle menu">
        <span></span><span></span><span></span>
      </button>

      <ul class="nav-links" id="nav-links">
        <li><a href="/#features">Features</a></li>
        <li><a href="/#how-it-works">How it works</a></li>
        <li><a href="/#pricing">Pricing</a></li>
        <li><a href="/locations/">Locations</a></li>
        <li><a href="/#faq">FAQ</a></li>
        <li><a class="btn btn-primary btn-sm nav-cta" href="/#waitlist">Join the waitlist</a></li>
      </ul>
    </div>
  </header>
"""


def footer_html(include_blog=False):
    blog_li = '\n            <li><a href="/blog/">Blog</a></li>' if include_blog else ""
    return f"""  <footer class="footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a class="logo" href="/" aria-label="RenoBeam home">
            {logo_svg("logo-grad-f")}
            <span>Reno<span class="logo-beam-word">Beam</span></span>
          </a>
          <p>The AI renovation estimator built by a working remodeling contractor. Photos and a short video in — a line-item estimate and client-ready proposal out.</p>
        </div>

        <nav aria-label="Product">
          <h4>Product</h4>
          <ul>
            <li><a href="/#features">Features</a></li>
            <li><a href="/#how-it-works">How it works</a></li>
            <li><a href="/#pricing">Pricing</a></li>
            <li><a href="/locations/">Locations</a></li>{blog_li}
          </ul>
        </nav>

        <nav aria-label="Get started">
          <h4>Get started</h4>
          <ul>
            <li><a href="/#faq">FAQ</a></li>
            <li><a href="/#founder">Why RenoBeam</a></li>
            <li><a href="/#waitlist">Join the waitlist</a></li>
            <li><a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a></li>
            <li><a href="/privacy">Privacy</a></li>
            <li><a href="/terms">Terms</a></li>
          </ul>
        </nav>
      </div>

      <div class="footer-bottom">
        <span>&copy; 2026 RenoBeam. All rights reserved.</span>
        <span>Designed &amp; Built by <a href="https://stylemarking.com" rel="noopener">StyleMarking.com</a></span>
      </div>
    </div>
  </footer>

  <script src="../js/main.js" defer></script>
"""


def head_html(title, meta, canonical, jsonld):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#0a0a0d">
  <title>{title}</title>
  <meta name="description" content="{meta}">
  <link rel="canonical" href="{canonical}">

  <meta property="og:type" content="website">
  <meta property="og:site_name" content="RenoBeam">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{meta}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{OG_IMAGE}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">

  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{title}">
  <meta name="twitter:description" content="{meta}">
  <meta name="twitter:image" content="{OG_IMAGE}">

  <link rel="icon" type="image/svg+xml" href="{FAVICON}">

  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">

  <link rel="stylesheet" href="../css/style.css">
  <style>{LOC_CSS}  </style>

{ANALYTICS}
  <script type="application/ld+json">
{jsonld}
  </script>
</head>
<body>
"""


def jsonld_for(loc_name, slug, meta, area):
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Locations", "item": SITE + "/locations/"},
                    {"@type": "ListItem", "position": 3, "name": loc_name, "item": SITE + "/locations/" + slug},
                ],
            },
            {
                "@type": "Service",
                "name": "Renovation estimating software in " + loc_name,
                "serviceType": "Renovation cost estimating software",
                "provider": {"@type": "Organization", "name": "RenoBeam", "url": SITE + "/"},
                "areaServed": area,
                "description": meta,
                "offers": [
                    {"@type": "Offer", "name": "Solo", "price": "79.00", "priceCurrency": "USD",
                     "description": "25 estimates per month, photo and video capture, line-item breakdowns."},
                    {"@type": "Offer", "name": "Crew", "price": "199.00", "priceCurrency": "USD",
                     "description": "100 estimates per month, 5 team seats, branded PDF proposals, price-book customization."},
                    {"@type": "Offer", "name": "Firm", "price": "499.00", "priceCurrency": "USD",
                     "description": "Unlimited estimates, API access, priority support."},
                ],
            },
        ],
    }
    return json.dumps(data, indent=2)


def pricing_html(loc, key=None):
    key = key or loc
    head = pick(key, "phead", PRICE_HEADS).format(loc=loc)
    intro = pick(key, "pintro", PRICE_INTROS)
    return f"""    <section class="section" id="plans">
      <div class="container">
        <div class="section-head" data-reveal>
          <span class="eyebrow">Planned pricing at launch</span>
          <h2>{head}</h2>
          <p>{intro}</p>
        </div>
        <div class="pricing-grid" data-reveal-group>
          <div class="price-card" data-reveal>
            <h3 class="price-name">Solo</h3>
            <p class="price-for">Independent contractors and handyman services</p>
            <p class="price-amount">$79<sub>/mo</sub></p>
            <ul class="price-features">
              <li>25 estimates per month</li>
              <li>Photo + video capture</li>
              <li>Line-item breakdowns with regional pricing</li>
            </ul>
            <a class="btn btn-ghost btn-block" href="/#waitlist">Join the waitlist</a>
          </div>
          <div class="price-card price-card--featured" data-reveal>
            <span class="price-badge">Most popular</span>
            <h3 class="price-name">Crew</h3>
            <p class="price-for">Remodeling companies and small GCs</p>
            <p class="price-amount">$199<sub>/mo</sub></p>
            <ul class="price-features">
              <li>100 estimates per month + 5 team seats</li>
              <li>Branded PDF proposals</li>
              <li>Price-book customization</li>
            </ul>
            <a class="btn btn-primary btn-block" href="/#waitlist">Join the waitlist</a>
          </div>
          <div class="price-card" data-reveal>
            <h3 class="price-name">Firm</h3>
            <p class="price-for">High-volume firms and insurance teams</p>
            <p class="price-amount">$499<sub>/mo</sub></p>
            <ul class="price-features">
              <li>Unlimited estimates</li>
              <li>API access</li>
              <li>Priority support</li>
            </ul>
            <a class="btn btn-ghost btn-block" href="/#waitlist">Join the waitlist</a>
          </div>
        </div>
      </div>
    </section>
"""


def cta_html(loc, key=None):
    key = key or loc
    head = pick(key, "ctah", CTA_HEADS).format(loc=loc)
    body = pick(key, "ctab", CTA_BODIES).format(loc=loc)
    return f"""    <section class="section">
      <div class="container">
        <div class="cta-panel" data-reveal>
          <h2>{head}</h2>
          <p>{body}</p>
          <p><a class="btn btn-primary btn-lg" href="/#waitlist">Join the waitlist</a></p>
        </div>
      </div>
    </section>
"""


def features_html(loc, market2, pair, key=None):
    """Pick 6 features from the pool of 8, rotated by location hash."""
    key = key or loc
    start = hnum(key, "fstart") % len(FEATURES)
    chosen = [FEATURES[(start + i) % len(FEATURES)] for i in range(6)]
    art = article(loc)
    head = pick(key, "fhead", FEAT_HEADS).format(loc=loc, art=art)
    cells = []
    for i, (title, bodies) in enumerate(chosen):
        body = bodies[hnum(key, "fbody" + str(i)) % len(bodies)].format(
            loc=loc, market2=market2, pair=pair, art=art)
        wide = ' bento-cell--wide' if i == 0 else ''
        cells.append(f"""          <div class="bento-cell{wide}" data-reveal>
            <h3>{title}</h3>
            <p>{body}</p>
          </div>""")
    cells_html = "\n".join(cells)
    return f"""    <section class="section">
      <div class="container">
        <div class="section-head" data-reveal>
          <span class="eyebrow">Features</span>
          <h2>{head}</h2>
        </div>
        <div class="bento" data-reveal-group>
{cells_html}
        </div>
      </div>
    </section>
"""


def breadcrumb_html(loc_name):
    return f"""        <nav class="loc-breadcrumb" aria-label="Breadcrumb">
          <a href="/">Home</a><span class="sep">/</span><a href="/locations/">Locations</a><span class="sep">/</span><span>{loc_name}</span>
        </nav>
"""


def links_section(loc, groups, key=None):
    """groups: list of (heading, [(label, href), ...])"""
    key = key or loc
    head = pick(key, "nearhead", NEARBY_HEADS).format(loc=loc)
    parts = [f"""    <section class="section loc-links">
      <div class="container">
        <div class="section-head" data-reveal>
          <span class="eyebrow">Service areas</span>
          <h2>{head}</h2>
        </div>"""]
    for heading, links in groups:
        if not links:
            continue
        chips = "\n".join(
            f'          <a class="loc-chip" href="{href}">{label}</a>' for label, href in links)
        parts.append(f"""        <h3>{heading}</h3>
        <div class="loc-chips">
{chips}
        </div>""")
    parts.append("""      </div>
    </section>
""")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------


def build_state_page(st):
    name = st["name"]
    slug = state_slug(name)
    canonical = f"{SITE}/locations/{slug}"
    title = f"Renovation Estimating Software in {name} — RenoBeam"
    meta = pick(name, "meta", METAS).format(loc=name, art=article(name))
    area = {"@type": "State", "name": name}
    jsonld = jsonld_for(name, slug, meta, area)

    market = name + " market"
    market2 = name + " market"
    pair = f"in {st['cities'][0]}"
    h1 = pick(name, "h1", H1S).format(loc=name)
    intro_a = pick(name, "introa", INTRO_A).format(loc=name, market=market, market2=market2)
    intro_b = pick(name, "introb", INTRO_B).format(loc=name)

    c = st["cities"]
    why = pick(name, "why", WHY_STATE).format(
        name=name, stock=st["stock"], climate=st["climate"],
        climate_cap=st["climate"][0].upper() + st["climate"][1:],
        c0=c[0], c1=c[1], c2=c[2], c3=c[min(3, len(c) - 1)], clist=oxford(c))
    why_head = pick(name, "whyhead", WHY_HEADS).format(loc=name)

    # internal links: this state's cities in our list + 4 nearby states
    my_cities = [ct for ct in CITIES if ct["state"] == name]
    city_links = [(f"{ct['name']}, {ct['abbr']}", f"/locations/{city_slug(ct)}") for ct in my_cities]
    nb_links = [(nb, f"/locations/{state_slug(nb)}") for nb in st["neighbors"]]
    groups = []
    if city_links:
        groups.append((f"{name} metro pages", city_links))
    groups.append(("Nearby states", nb_links))

    body = f"""  <main id="main">
    <section class="loc-hero">
      <div class="container">
{breadcrumb_html(name)}        <span class="hero-badge"><span class="pulse-dot" aria-hidden="true"></span>Coming soon to {name}</span>
        <h1>{h1}</h1>
        <div class="loc-intro">
          <p>{intro_a}</p>
          <p>{intro_b}</p>
        </div>
{PRELAUNCH_NOTE}
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head" data-reveal>
          <span class="eyebrow">The local angle</span>
          <h2>{why_head}</h2>
        </div>
        <div class="loc-prose" data-reveal>
{why}
        </div>
      </div>
    </section>

{features_html(name, market2, pair)}
{how_html(name, market2)}
{pricing_html(name)}
{links_section(name, groups)}  </main>

"""
    return head_html(title, meta, canonical, jsonld) + nav_html() + body + footer_html() + "</body>\n</html>\n"


def build_city_page(ct):
    name = ct["name"]
    full = f"{name}, {ct['abbr']}"
    slug = city_slug(ct)
    canonical = f"{SITE}/locations/{slug}"
    title = f"Renovation Estimating Software in {full} — RenoBeam"
    meta = pick(full, "meta", METAS).format(loc=name, art=article(name))
    area = {"@type": "City", "name": name,
            "containedInPlace": {"@type": "State", "name": ct["state"]}}
    jsonld = jsonld_for(full, slug, meta, area)

    market = name + " market"
    market2 = name + " market"
    h = ct["hoods"]
    pair = f"in {h[0]}"
    h1 = pick(full, "h1", H1S).format(loc=name)
    intro_a = pick(full, "introa", INTRO_A).format(loc=name, market=market, market2=market2)
    intro_b = pick(full, "introb", INTRO_B).format(loc=name)
    why = pick(full, "why", WHY_CITY).format(
        name=name, full=f"{name}, {ct['state']}", color=ct["color"],
        h0=h[0], h1=h[1], h2=h[2], h3=h[3], h4=h[4])
    why_head = pick(full, "whyhead", WHY_HEADS).format(loc=name)

    # internal links: state page + 5 other cities (same-state siblings first)
    siblings = [c2 for c2 in CITIES if c2["state"] == ct["state"] and c2["name"] != name]
    others = []
    idx = next(i for i, c2 in enumerate(CITIES) if c2["name"] == name and c2["abbr"] == ct["abbr"])
    for step in range(1, len(CITIES)):
        cand = CITIES[(idx + step) % len(CITIES)]
        if cand["state"] != ct["state"]:
            others.append(cand)
    linked = (siblings + others)[:5]
    city_links = [(f"{c2['name']}, {c2['abbr']}", f"/locations/{city_slug(c2)}") for c2 in linked]
    state_link = [(f"All of {ct['state']}", f"/locations/{state_slug(ct['state'])}")]
    groups = [(f"The rest of {ct['state']}", state_link), ("More metros", city_links)]

    body = f"""  <main id="main">
    <section class="loc-hero">
      <div class="container">
{breadcrumb_html(full)}        <span class="hero-badge"><span class="pulse-dot" aria-hidden="true"></span>Coming soon to {full}</span>
        <h1>{h1}</h1>
        <div class="loc-intro">
          <p>{intro_a}</p>
          <p>{intro_b}</p>
        </div>
{PRELAUNCH_NOTE}
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head" data-reveal>
          <span class="eyebrow">The local angle</span>
          <h2>{why_head}</h2>
        </div>
        <div class="loc-prose" data-reveal>
{why}
        </div>
      </div>
    </section>

{features_html(name, market2, pair, key=full)}
{how_html(name, market2, key=full)}
{pricing_html(name, key=full)}
{links_section(name, groups, key=full)}  </main>

"""
    return head_html(title, meta, canonical, jsonld) + nav_html() + body + footer_html() + "</body>\n</html>\n"


def build_hub_page():
    title = "RenoBeam Service Areas — Renovation Estimating Software by Location"
    meta = ("Find RenoBeam in your market: AI renovation estimating software with regional pricing, planned for all "
            "50 states and every major US metro. Pre-launch — join the early-access list.")
    canonical = f"{SITE}/locations/"
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Locations", "item": SITE + "/locations/"},
                ],
            },
            {
                "@type": "CollectionPage",
                "name": title,
                "url": canonical,
                "description": meta,
                "isPartOf": {"@type": "WebSite", "name": "RenoBeam", "url": SITE + "/"},
            },
        ],
    }
    jsonld = json.dumps(data, indent=2)

    cards = []
    for st in STATES:
        s_slug = state_slug(st["name"])
        my_cities = [ct for ct in CITIES if ct["state"] == st["name"]]
        lis = "\n".join(
            f'            <li><a href="/locations/{city_slug(ct)}">{ct["name"]}, {ct["abbr"]}</a></li>'
            for ct in my_cities)
        list_html = f"\n          <ul>\n{lis}\n          </ul>" if lis else ""
        cards.append(f"""        <div class="loc-hub-card">
          <h3><a href="/locations/{s_slug}">{st["name"]}</a></h3>{list_html}
        </div>""")
    cards_html = "\n".join(cards)

    metro_chips = "\n".join(
        f'          <a class="loc-chip" href="/locations/{city_slug(ct)}"><strong>{ct["name"]}</strong>, {ct["abbr"]}</a>'
        for ct in CITIES)

    body = f"""  <main id="main">
    <section class="loc-hero">
      <div class="container">
        <nav class="loc-breadcrumb" aria-label="Breadcrumb">
          <a href="/">Home</a><span class="sep">/</span><span>Locations</span>
        </nav>
        <span class="hero-badge"><span class="pulse-dot" aria-hidden="true"></span>Launching nationwide</span>
        <h1>Renovation estimating software, <span class="grad-text">priced for your market</span></h1>
        <div class="loc-intro">
          <p>RenoBeam is a cloud product — at launch it will work wherever you and your phone do. But renovation pricing is local, and so is the way we talk about it. Pick your state or metro below to see how RenoBeam's regional price adjustment, line-item estimates, and branded PDF proposals are being built to fit the market you actually bid in.</p>
          <p>Every market starts the same way: join the early-access list, and we'll email you when RenoBeam opens there.</p>
        </div>
{PRELAUNCH_NOTE}
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head" data-reveal>
          <span class="eyebrow">Major metros</span>
          <h2>The 25 biggest rental and renovation markets</h2>
        </div>
        <div class="loc-chips" data-reveal>
{metro_chips}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head" data-reveal>
          <span class="eyebrow">All 50 states</span>
          <h2>Pick your state</h2>
        </div>
        <div class="loc-hub-grid">
{cards_html}
        </div>
      </div>
    </section>

{cta_html("your market")}  </main>

"""
    return head_html(title, meta, canonical, jsonld) + nav_html() + body + footer_html(include_blog=True) + "</body>\n</html>\n"


# ---------------------------------------------------------------------------
# Root files
# ---------------------------------------------------------------------------


def build_sitemap(slugs):
    urls = ([SITE + "/", SITE + "/blog/"]
            + [SITE + "/blog/" + s for s in BLOG_POSTS]
            + [SITE + "/privacy", SITE + "/terms"]
            + [SITE + "/locations/"]
            + [SITE + "/locations/" + s for s in slugs])
    entries = "\n".join(
        f"  <url>\n    <loc>{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n  </url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{entries}\n</urlset>\n'


def build_robots():
    return f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    os.makedirs(OUT, exist_ok=True)
    written = []

    slugs = []
    for st in STATES:
        slug = state_slug(st["name"])
        slugs.append(slug)
        path = os.path.join(OUT, slug + ".html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_state_page(st))
        written.append(path)

    for ct in CITIES:
        slug = city_slug(ct)
        slugs.append(slug)
        path = os.path.join(OUT, slug + ".html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_city_page(ct))
        written.append(path)

    hub = os.path.join(OUT, "index.html")
    with open(hub, "w", encoding="utf-8") as f:
        f.write(build_hub_page())
    written.append(hub)

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap(slugs))
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(build_robots())

    print(f"Wrote {len(written)} pages ({len(STATES)} states, {len(CITIES)} cities, 1 hub) + sitemap.xml + robots.txt")


if __name__ == "__main__":
    main()
