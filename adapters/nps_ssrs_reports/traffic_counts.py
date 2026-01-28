import json
import time
import sys
import re
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

NPS_TRAFFIC_LOCATIONS = {
    "ACAD": {
        "Acadia NP SAND BEACH": {"lat": 44.3302, "lng": -68.1840},
        "Acadia NP SCHOODIC": {"lat": 44.3364, "lng": -68.0602}
    },
    "BADL": {
        "Badlands NP INTERIOR ENTRANCE": {"lat": 43.7480, "lng": -101.9410},
        "Badlands NP NORTHEAST ENTRANCE": {"lat": 43.8341, "lng": -101.9052},
        "Badlands NP PINNACLES ENTRANCE": {"lat": 43.8681, "lng": -102.2343}
    },
    "CANY": {
        "Canyonlands NP ELEPHANT HILL": {"lat": 38.1402, "lng": -109.7611},
        "Canyonlands NP HORSESHOE CANYON": {"lat": 38.4489, "lng": -110.2014},
        "Canyonlands NP ISLAND PROPER ENTRANCE": {"lat": 38.4725, "lng": -109.8210},
        "Canyonlands NP MAZE OVERLOOK": {"lat": 38.2195, "lng": -109.9961},
        "Canyonlands NP NEEDLES PROPER": {"lat": 38.1681, "lng": -109.7594},
        "Canyonlands NP POTASH": {"lat": 38.5147, "lng": -109.6019},
        "Canyonlands NP SHAFER TRAIL": {"lat": 38.5042, "lng": -109.7364},
        "Canyonlands NP STANDING ROCKS": {"lat": 38.1883, "lng": -110.0039},
        "Canyonlands NP WHITE RIM EAST SIDE": {"lat": 38.3846, "lng": -109.7785},
        "Canyonlands NP WHITE RIM WEST SIDE": {"lat": 38.4475, "lng": -110.0210}
    },
    "ARCH": {
        "Arches NP SALT VALLEY": {"lat": 38.8315, "lng": -109.6895},
        "Arches NP WILLOW FLATS": {"lat": 38.7118, "lng": -109.6384},
        "Arches NP MAIN ENTRANCE": {"lat": 38.6165, "lng": -109.6162}
    },
    "BLCA": {
        "Black Canyon of the Gunnison NP NORTH RIM DRIVE COUNTER": {"lat": 38.5841, "lng": -107.7029},
        "Black Canyon of the Gunnison NP SOUTH RIM DRIVE COUNTER": {"lat": 38.5505, "lng": -107.6866}
    },
    "GLAC": {
        "Glacier NP BELLY RIVER": {"lat": 48.9814, "lng": -113.6821},
        "Glacier NP CAMAS": {"lat": 48.6019, "lng": -114.1558},
        "Glacier NP GOAT LICK": {"lat": 48.3374, "lng": -113.5186},
        "Glacier NP MANY GLACIER": {"lat": 48.7971, "lng": -113.6558},
        "Glacier NP POLEBRIDGE": {"lat": 48.7618, "lng": -114.2831},
        "Glacier NP SAINT MARY LANE 1": {"lat": 48.7465, "lng": -113.4339},
        "Glacier NP SAINT MARY LANE 2": {"lat": 48.7465, "lng": -113.4339},
        "Glacier NP SAINT MARY LANE 3": {"lat": 48.7465, "lng": -113.4339},
        "Glacier NP TWO MEDICINE": {"lat": 48.4842, "lng": -113.3421},
        "Glacier NP WATERTON": {"lat": 48.9972, "lng": -113.6601},
        "Glacier NP WEST ENTRANCE": {"lat": 48.4981, "lng": -113.9856}
    },
    "GRTE": {
        "Grand Teton NP BUFFALO ENTRANCE": {"lat": 43.8344, "lng": -110.4571},
        "Grand Teton NP GROS VENTRE JUNCTION": {"lat": 43.5599, "lng": -110.7410},
        "Grand Teton NP JDR (SOUTHBOUND) (REC'D FROM JDR)": {"lat": 44.1132, "lng": -110.6659},
        "Grand Teton NP MOOSE ENTRANCE": {"lat": 43.6565, "lng": -110.7181},
        "Grand Teton NP MOOSE WILSON ENTRANCE": {"lat": 43.6019, "lng": -110.8245},
        "Grand Teton NP US 89 (WESTBOUND)": {"lat": 43.6822, "lng": -110.7099}
    },
    "GRSA": {
        "Great Sand Dunes NP & PRES PARK ENTRANCE": {"lat": 37.7276, "lng": -105.5147},
        "Great Sand Dunes NP & PRES MEDANO PASS ROAD": {"lat": 37.7554, "lng": -105.4795}
    },
    "MEVE": {
        "Mesa Verde NP WETHERILL": {"lat": 37.1995, "lng": -108.5245},
        "Mesa Verde NP MAIN ENTRANCE ON HWY 10": {"lat": 37.3364, "lng": -108.4069}
    },
    "ROMO": {
        "Rocky Mountain NP BEAVER MEADOWS": {"lat": 40.3601, "lng": -105.5786},
        "Rocky Mountain NP FALL RIVER": {"lat": 40.4045, "lng": -105.5841},
        "Rocky Mountain NP GRAND LAKE": {"lat": 40.2452, "lng": -105.8236},
        "Rocky Mountain NP LONGS PEAK": {"lat": 40.2448, "lng": -105.5463},
        "Rocky Mountain NP SUN VALLEY ROAD": {"lat": 40.2319, "lng": -105.8645},
        "Rocky Mountain NP WILD BASIN": {"lat": 40.2081, "lng": -105.5386}
    },
    "BRCA": {
        "Bryce Canyon NP ENTRANCE STATION": {"lat": 37.6441, "lng": -112.1623},
        "Bryce Canyon NP RAINBOW GATE": {"lat": 37.4760, "lng": -112.2403},
        "Bryce Canyon NP UTAH 12": {"lat": 37.7410, "lng": -112.3021}
    },
    "CARE": {
        "Capitol Reef NP BULLFROG": {"lat": 37.5255, "lng": -110.7208},
        "Capitol Reef NP BURR TRAIL": {"lat": 37.8647, "lng": -111.0858},
        "Capitol Reef NP CEDAR MESA": {"lat": 37.9423, "lng": -111.0456},
        "Capitol Reef NP PETROGLYPHS": {"lat": 38.2891, "lng": -111.2372},
        "Capitol Reef NP VISITOR CENTER": {"lat": 38.2825, "lng": -111.2464},
        "Capitol Reef NP GOOSENECKS": {"lat": 38.2911, "lng": -111.2721},
        "Capitol Reef NP NORTH DISTRICT": {"lat": 38.4552, "lng": -111.3725},
        "Capitol Reef NP SCENIC DRIVE": {"lat": 38.2725, "lng": -111.2330},
        "Capitol Reef NP US 24 EAST ONLY": {"lat": 38.2858, "lng": -111.2215},
        "Capitol Reef NP US 24 EAST/WEST": {"lat": 38.2858, "lng": -111.2215}
    },
    "ZION": {
        "Zion NP CANYON DRIVE": {"lat": 37.2148, "lng": -112.9791},
        "Zion NP EAST ENTRANCE": {"lat": 37.2334, "lng": -112.8756},
        "Zion NP KOLOB CANYON": {"lat": 37.4525, "lng": -113.2119},
        "Zion NP KOLOB TERRACE": {"lat": 37.2403, "lng": -113.1119},
        "Zion NP SOUTH ENTRANCE": {"lat": 37.2003, "lng": -112.9867}
    },
    "THRO": {
        "Theodore Roosevelt NP PAINTED CANYON REST AREA": {"lat": 46.8942, "lng": -103.3789},
        "Theodore Roosevelt NP SCENIC DRIVE (VISITOR CENTER AREA": {"lat": 46.9102, "lng": -103.5262},
        "Theodore Roosevelt NP SCENIC LOOP DRIVE (MEDORA)": {"lat": 46.9081, "lng": -103.4795}
    },
    "WICA": {
        "Wind Cave NP HIGHWAY 385 SOUTH (COUNTER #5)": {"lat": 43.5186, "lng": -103.4831},
        "Wind Cave NP HIGHWAY 385 WEST (COUNTER #4)": {"lat": 43.5583, "lng": -103.5358},
        "Wind Cave NP HIGHWAY 87 NORTH (COUNTER #2)": {"lat": 43.6192, "lng": -103.4619}
    },
    "YELL": {
        "Yellowstone NP EAST GATE": {"lat": 44.4883, "lng": -110.0039},
        "Yellowstone NP NORTH GATE": {"lat": 45.0294, "lng": -110.7092},
        "Yellowstone NP NORTHEAST GATE": {"lat": 45.0031, "lng": -110.0076},
        "Yellowstone NP SOUTH GATE": {"lat": 44.1336, "lng": -110.6658},
        "Yellowstone NP WEST GATE": {"lat": 44.6583, "lng": -111.0971},
        "Yellowstone NP HIGHWAY 191": {"lat": 44.8214, "lng": -111.0995}
    },
    "SHEN": {
        "Shenandoah NP PANORAMA REST": {"lat": 38.6631, "lng": -78.3206},
        "Shenandoah NP ROCKFISH ENTRANCE": {"lat": 38.0325, "lng": -78.8586},
        "Shenandoah NP SWIFT RUN ENTRANCE": {"lat": 38.3567, "lng": -78.4631},
        "Shenandoah NP THORNTON GAP ENTRANCE": {"lat": 38.6601, "lng": -78.3214},
        "Shenandoah NP FRONT ROYAL ENTRANCE": {"lat": 38.9102, "lng": -78.1969}
    },
    "CONG": {
        "Congaree NP ENTRANCE": {"lat": 33.8291, "lng": -80.8236},
        "Congaree NP BANNISTER": {"lat": 33.7952, "lng": -80.7584},
        "Congaree NP SOUTH CEDAR CREEK": {"lat": 33.8052, "lng": -80.8521}
    },
    "BISC": {
        "Biscayne NP VISITOR CENTER": {"lat": 25.4646, "lng": -80.3344}
    },
    "EVER": {
        "Everglades NP MAIN ENTRANCE / HOMESTEAD": {"lat": 25.3941, "lng": -80.5841},
        "Everglades NP BUTTONWOOD BRIDGE": {"lat": 25.1432, "lng": -80.9251},
        "Everglades NP SHARK VALLEY": {"lat": 25.7554, "lng": -80.7661},
        "Everglades NP GULF COAST": {"lat": 25.8452, "lng": -81.3852},
        "Everglades NP EAST EVERGLADES": {"lat": 25.7611, "lng": -80.5052}
    },
    "GRSM": {
        "Great Smoky Mountains NP TWENTYMILE": {"lat": 35.4682, "lng": -83.8761},
        "Great Smoky Mountains NP ABRAMS CREEK": {"lat": 35.6108, "lng": -83.9341},
        "Great Smoky Mountains NP BIG CREEK": {"lat": 35.7512, "lng": -83.1102},
        "Great Smoky Mountains NP CADES COVE LOOP (STATION 411 LANES 3 AND 4)": {"lat": 35.5947, "lng": -83.7745},
        "Great Smoky Mountains NP CATALOOCHEE": {"lat": 35.6322, "lng": -83.0789},
        "Great Smoky Mountains NP CHEROKEE ORCHARD (STATION 418 LANE 2)": {"lat": 35.6841, "lng": -83.4862},
        "Great Smoky Mountains NP KUWOHI / SMOKEMONT (STATION 417 LANE 1)": {"lat": 35.5131, "lng": -83.3056},
        "Great Smoky Mountains NP COSBY": {"lat": 35.7521, "lng": -83.2081},
        "Great Smoky Mountains NP DEEP CREEK": {"lat": 35.4522, "lng": -83.4339},
        "Great Smoky Mountains NP FOOTHILLS PARKWAY WEST FROM FLATS ROAD": {"lat": 35.6521, "lng": -83.9312},
        "Great Smoky Mountains NP FOOTHILLS PARKWAY WEST FROM HWY 129": {"lat": 35.6120, "lng": -84.0021},
        "Great Smoky Mountains NP FOOTHILLS PARKWAY WEST FROM HWY 321": {"lat": 35.6720, "lng": -83.9821},
        "Great Smoky Mountains NP FOOTHILLS PARKWAY WEST FROM WEARS VALLEY (STATION 407 LANE 1)": {"lat": 35.6701, "lng": -83.6702},
        "Great Smoky Mountains NP FOOTHILLS PARKWAY WEST FROM WALLAND (STATION 406 LANE 1)": {"lat": 35.7275, "lng": -83.8201},
        "Great Smoky Mountains NP FOOTHILLS PARKWAY EAST (STATION 416 LANES 1 AND 2)": {"lat": 35.8402, "lng": -83.2401},
        "Great Smoky Mountains NP GATLINBURG BYPASS": {"lat": 35.7112, "lng": -83.5281},
        "Great Smoky Mountains NP GATLINBURG SPUR (STATION 405 LANES 1 AND 2 - ESTIMATED)": {"lat": 35.7486, "lng": -83.5134},
        "Great Smoky Mountains NP GATLINBURG / SUGARLANDS (STATION 401 LANE 2)": {"lat": 35.6852, "lng": -83.5372},
        "Great Smoky Mountains NP GREENBRIER": {"lat": 35.7482, "lng": -83.3852},
        "Great Smoky Mountains NP HEINTOOGA RIDGE (STATION 415 LANE 1)": {"lat": 35.5482, "lng": -83.1782},
        "Great Smoky Mountains NP LAKEVIEW DRIVE": {"lat": 35.4582, "lng": -83.4182},
        "Great Smoky Mountains NP OCONALUFTEE (STATION 403 LANE 3)": {"lat": 35.5131, "lng": -83.3056},
        "Great Smoky Mountains NP OCONALUFTEE (STATION 403 LANE 4)": {"lat": 35.5131, "lng": -83.3056},
        "Great Smoky Mountains NP PARSONS BRANCH": {"lat": 35.5121, "lng": -83.8521},
        "Great Smoky Mountains NP RICH MOUNTAIN": {"lat": 35.6282, "lng": -83.7852},
        "Great Smoky Mountains NP ROARING FORK NATURE TRAIL": {"lat": 35.6947, "lng": -83.4739},
        "Great Smoky Mountains NP TOWNSEND (STATION 404 LANE 2)": {"lat": 35.6669, "lng": -83.7122},
        "Great Smoky Mountains NP TREMONT (STATION 410 LANE 1)": {"lat": 35.6282, "lng": -83.6882},
        "Great Smoky Mountains NP WEAR COVE": {"lat": 35.6982, "lng": -83.6582}
    },
    "MACA": {
        "Mammoth Cave NP 3201 LANE 4 (S.H. 70 EASTBOUND LANE)": {"lat": 37.1252, "lng": -86.1152},
        "Mammoth Cave NP 3202 LANE 2 (EAST ENTRANCE ROAD WESTBOUND LANE)": {"lat": 37.1652, "lng": -86.0652},
        "Mammoth Cave NP 3202 LANE 3 (SOUTH ENTRANCE ROAD NORTHBOUND LANE)": {"lat": 37.1252, "lng": -86.1152},
        "Mammoth Cave NP 3201 LANE 2 (S.H. 70 WESTBOUND LANE)": {"lat": 37.1252, "lng": -86.1152}
    },
    "CUVA": {
        "Cuyahoga Valley NP HAPPY DAYS NORTH": {"lat": 41.2261, "lng": -81.5031},
        "Cuyahoga Valley NP HUNT FARM TRAILHEAD": {"lat": 41.1991, "lng": -81.5652},
        "Cuyahoga Valley NP IRA TRAILHEAD": {"lat": 41.1852, "lng": -81.5841},
        "Cuyahoga Valley NP KENDALL LAKE": {"lat": 41.2201, "lng": -81.5232},
        "Cuyahoga Valley NP LEDGES": {"lat": 41.2225, "lng": -81.5103},
        "Cuyahoga Valley NP LOCK 29 OVERFLOW": {"lat": 41.2682, "lng": -81.5541},
        "Cuyahoga Valley NP LOCK 29 TRAILHEAD": {"lat": 41.2682, "lng": -81.5541},
        "Cuyahoga Valley NP LOCK 39 TRAILHEAD": {"lat": 41.3532, "lng": -81.6112},
        "Cuyahoga Valley NP OAK HILL": {"lat": 41.2012, "lng": -81.5881},
        "Cuyahoga Valley NP BLUE HEN FALLS": {"lat": 41.2612, "lng": -81.5752},
        "Cuyahoga Valley NP BOSTON STORE": {"lat": 41.2625, "lng": -81.5586},
        "Cuyahoga Valley NP PINE HOLLOW EAST": {"lat": 41.2281, "lng": -81.5121},
        "Cuyahoga Valley NP PINE HOLLOW WEST": {"lat": 41.2281, "lng": -81.5121},
        "Cuyahoga Valley NP REDLOCK TRAILHEAD": {"lat": 41.3001, "lng": -81.5652},
        "Cuyahoga Valley NP STATION ROAD TRAILHEAD": {"lat": 41.3182, "lng": -81.5881},
        "Cuyahoga Valley NP WETMORE TRAILHEAD": {"lat": 41.2182, "lng": -81.5452},
        "Cuyahoga Valley NP BOSTON TRAILHEAD": {"lat": 41.2625, "lng": -81.5586},
        "Cuyahoga Valley NP BRANDYWINE OVERFLOW": {"lat": 41.2764, "lng": -81.5583},
        "Cuyahoga Valley NP CROWFOOT GULLY": {"lat": 41.2421, "lng": -81.5152},
        "Cuyahoga Valley NP EVERETT BRIDGE": {"lat": 41.2052, "lng": -81.5841},
        "Cuyahoga Valley NP FRAZEE HOUSE": {"lat": 41.3512, "lng": -81.6082},
        "Cuyahoga Valley NP HAPPY DAYS SOUTH": {"lat": 41.2261, "lng": -81.5031},
        "Cuyahoga Valley NP HIKE AND BIKE TRAILHEAD": {"lat": 41.2201, "lng": -81.5012},
        "Cuyahoga Valley NP HORSESHOE POND": {"lat": 41.2152, "lng": -81.5721},
        "Cuyahoga Valley NP INDIGO LAKE": {"lat": 41.2021, "lng": -81.5712},
        "Cuyahoga Valley NP LITTLE MEADOWS TRAFFIC": {"lat": 41.2152, "lng": -81.5152},
        "Cuyahoga Valley NP PINE LANE": {"lat": 41.2521, "lng": -81.5612},
        "Cuyahoga Valley NP STANFORD HOUSE": {"lat": 41.2712, "lng": -81.5581},
        "Cuyahoga Valley NP OCTAGON PARKING TRAFFIC": {"lat": 41.2251, "lng": -81.5121},
        "Cuyahoga Valley NP BOTZUM": {"lat": 41.1621, "lng": -81.5721},
        "Cuyahoga Valley NP BRANDYWINE": {"lat": 41.2764, "lng": -81.5583},
        "Cuyahoga Valley NP CANAL EXPLORATION CENTER": {"lat": 41.3532, "lng": -81.6112}
    },
    "INDU": {
        "Indiana Dunes NP BAILLY/CHELLBERG": {"lat": 41.6251, "lng": -87.0512},
        "Indiana Dunes NP BUELL VISITOR CENTER": {"lat": 41.6112, "lng": -87.0652},
        "Indiana Dunes NP CENTRAL BEACH": {"lat": 41.6912, "lng": -86.9552},
        "Indiana Dunes NP COWLES BOG": {"lat": 41.6444, "lng": -87.0847},
        "Indiana Dunes NP DUNBAR": {"lat": 41.6852, "lng": -86.9821},
        "Indiana Dunes NP GREENBELT PARKING AREA": {"lat": 41.6182, "lng": -87.2152},
        "Indiana Dunes NP HORSE/SKI TRAIL": {"lat": 41.6282, "lng": -87.0212},
        "Indiana Dunes NP TOLLESTON DUNES": {"lat": 41.6121, "lng": -87.1652},
        "Indiana Dunes NP KEMIL LOT": {"lat": 41.6821, "lng": -87.0012},
        "Indiana Dunes NP LAKEFRONT DRIVE": {"lat": 41.6852, "lng": -86.9652},
        "Indiana Dunes NP MOUNT BALDY": {"lat": 41.7067, "lng": -86.9292},
        "Indiana Dunes NP PORTAGE LAKE FRONT": {"lat": 41.6321, "lng": -87.1782},
        "Indiana Dunes NP PORTER BEACH NORTH": {"lat": 41.6621, "lng": -87.0652},
        "Indiana Dunes NP PORTER BEACH SOUTH": {"lat": 41.6601, "lng": -87.0652},
        "Indiana Dunes NP TREMONT LOT": {"lat": 41.6421, "lng": -87.0421},
        "Indiana Dunes NP WEST BEACH": {"lat": 41.6219, "lng": -87.2025}
    },
    "BIBE": {
        "Big Bend NP ROUTE 11-PERSIMMON GAP": {"lat": 29.6586, "lng": -103.1721},
        "Big Bend NP ROUTE 13-MAVERICK": {"lat": 29.3361, "lng": -103.5132}
    },
    "CAVE": {
        "Carlsbad Caverns NP MAIN ENTRANCE": {"lat": 32.1752, "lng": -104.4412},
        "Carlsbad Caverns NP RATTLESNAKE SPRINGS": {"lat": 32.1121, "lng": -104.4721}
    },
    "GUMO": {
        "Guadalupe Mountains NP DOG CANYON": {"lat": 32.0452, "lng": -104.8352},
        "Guadalupe Mountains NP FRIJOLE": {"lat": 31.9052, "lng": -104.8052},
        "Guadalupe Mountains NP MCKITTRICK CANYON": {"lat": 31.9782, "lng": -104.7521},
        "Guadalupe Mountains NP PINE SPRINGS": {"lat": 31.8951, "lng": -104.8281},
        "Guadalupe Mountains NP SALT BASIN DUNES": {"lat": 31.9121, "lng": -105.1152}
    },
    "HOSP": {
        "Hot Springs NP HOT SPRINGS MOUNTAIN": {"lat": 34.5152, "lng": -93.0452},
        "Hot Springs NP WEST MOUNTAIN DRIVE (NORTH)": {"lat": 34.5121, "lng": -93.0652},
        "Hot Springs NP WEST MOUNTAIN DRIVE (SOUTH)": {"lat": 34.5021, "lng": -93.0752},
        "Hot Springs NP WEST MOUNTAIN SUMMIT DRIVE (NORTH)": {"lat": 34.5082, "lng": -93.0682},
        "Hot Springs NP GULPHA GORGE HWY (NORTH)": {"lat": 34.5252, "lng": -93.0321},
        "Hot Springs NP GULPHA GORGE HWY (SOUTH)": {"lat": 34.5221, "lng": -93.0321}
    },
    "WHSA": {
        "White Sands NP MAIN ENTRANCE FROM HWY 70": {"lat": 32.7794, "lng": -106.1719},
        "White Sands NP DUNE AREA": {"lat": 32.8252, "lng": -106.2652}
    },
    "DEVA": {
        "Death Valley NP ASHFORD ROAD": {"lat": 35.9182, "lng": -116.6782},
        "Death Valley NP BIG PINE ROAD": {"lat": 37.1721, "lng": -117.6521},
        "Death Valley NP DAYLIGHT PASS": {"lat": 36.7956, "lng": -116.8686},
        "Death Valley NP GRAPEVINE CANYON": {"lat": 37.0321, "lng": -117.3752},
        "Death Valley NP RYAN": {"lat": 36.3152, "lng": -116.6752},
        "Death Valley NP SLAINE VALLEY": {"lat": 36.6582, "lng": -117.7521},
        "Death Valley NP TITUS CANYON": {"lat": 36.8221, "lng": -117.1721},
        "Death Valley NP TOWNES PASS": {"lat": 36.4022, "lng": -117.4336},
        "Death Valley NP WILDROSE": {"lat": 36.2697, "lng": -117.1864},
        "Death Valley NP PHINNEY CANYON": {"lat": 36.7821, "lng": -116.9252}
    },
    "GRCA": {
        "Grand Canyon NP NORTH RIM": {"lat": 36.3571, "lng": -112.0571},
        "Grand Canyon NP SOUTH DISTRICT": {"lat": 35.9897, "lng": -112.1211},
        "Grand Canyon NP TUWEEP": {"lat": 36.2132, "lng": -113.0612},
        "Grand Canyon NP DESERT VIEW": {"lat": 36.0406, "lng": -111.8267}
    },
    "HALE": {
        "Haleakala NP COASTAL ENTRANCE (KIPAHULU)": {"lat": 20.6612, "lng": -156.0452},
        "Haleakala NP SUMMIT ENTRANCE": {"lat": 20.7621, "lng": -156.2452}
    },
    "HAVO": {
        "Hawaii Volcanoes NP CHAINS OF CRATER ROAD": {"lat": 19.3521, "lng": -155.2052},
        "Hawaii Volcanoes NP ENTRANCE LANE 1": {"lat": 19.4291, "lng": -155.2571},
        "Hawaii Volcanoes NP ENTRANCE LANE 2": {"lat": 19.4291, "lng": -155.2571}
    },
    "JOTR": {
        "Joshua Tree NP BLACK ROCK": {"lat": 34.0721, "lng": -116.3912},
        "Joshua Tree NP COTTONWOOD": {"lat": 33.6706, "lng": -115.8048},
        "Joshua Tree NP COVINGTON": {"lat": 34.0952, "lng": -116.3121},
        "Joshua Tree NP INDIAN COVE": {"lat": 34.0952, "lng": -116.1582},
        "Joshua Tree NP JOSHUA TREE": {"lat": 34.1292, "lng": -116.3152},
        "Joshua Tree NP 29 PALMS": {"lat": 34.1293, "lng": -116.0374}
    },
    "LAVO": {
        "Lassen Volcanic NP BUTTE LAKE": {"lat": 40.5621, "lng": -121.3012},
        "Lassen Volcanic NP JUNIPER LAKE": {"lat": 40.4512, "lng": -121.3121},
        "Lassen Volcanic NP MANZANITA": {"lat": 40.5352, "lng": -121.5641},
        "Lassen Volcanic NP SOUTHWEST": {"lat": 40.4352, "lng": -121.5352},
        "Lassen Volcanic NP WARNER VALLEY": {"lat": 40.4382, "lng": -121.3852},
        "Lassen Volcanic NP CROSSROADS": {"lat": 40.4852, "lng": -121.5121}
    },
    "GRBA": {
        "Great Basin NP BAKER CREEK": {"lat": 38.9852, "lng": -114.2421},
        "Great Basin NP GREAT BASIN VC": {"lat": 39.0152, "lng": -114.2182},
        "Great Basin NP LEHMAN": {"lat": 39.0052, "lng": -114.2212},
        "Great Basin NP LEHMAN CAVES VC": {"lat": 39.0052, "lng": -114.2212},
        "Great Basin NP ROUTE 488 MAIN ENTRANCE": {"lat": 39.0052, "lng": -114.2152},
        "Great Basin NP SNAKE CREEK": {"lat": 38.9152, "lng": -114.1852},
        "Great Basin NP STRAWBERRY CREEK": {"lat": 39.0652, "lng": -114.2152},
        "Great Basin NP WHEELER PEAK": {"lat": 39.0121, "lng": -114.3012}
    },
    "PEFO": {
        "Petrified Forest NP I-40 COUNTER": {"lat": 35.0652, "lng": -109.7821},
        "Petrified Forest NP NORTH ENTRANCE (NORTH LANE #2)": {"lat": 35.0652, "lng": -109.7821},
        "Petrified Forest NP SOUTH ENTRANCE (NORTH LANE #1)": {"lat": 34.7852, "lng": -109.8921}
    },
    "PINN": {
        "Pinnacles NP EAST ENTRANCE": {"lat": 36.4921, "lng": -121.1452},
        "Pinnacles NP WEST ENTRANCE": {"lat": 36.4852, "lng": -121.2152}
    },
    "REDW": {
        "Redwood NP COASTAL DRIVE": {"lat": 41.5152, "lng": -124.0952},
        "Redwood NP DAVISON ROAD": {"lat": 41.3352, "lng": -124.0252},
        "Redwood NP DOLASON PRAIRIE": {"lat": 41.2152, "lng": -123.9552},
        "Redwood NP ENDERTS / CRESCENT BEACH": {"lat": 41.7152, "lng": -124.1552},
        "Redwood NP FRESHWATER LAGOON": {"lat": 41.2952, "lng": -124.1012},
        "Redwood NP HIOUCHI VISITOR CENTER": {"lat": 41.7952, "lng": -124.0852},
        "Redwood NP KLAMATH BEACH ROAD": {"lat": 41.5352, "lng": -124.0821},
        "Redwood NP KLAMATH RIVER OVERLOOK": {"lat": 41.5121, "lng": -124.1012},
        "Redwood NP LAGOON CREEK PARKING AREA": {"lat": 41.5952, "lng": -124.1012},
        "Redwood NP LOST MAN CREEK ROAD": {"lat": 41.3252, "lng": -124.0121},
        "Redwood NP REDWOOD CREEK TRAIL": {"lat": 41.2852, "lng": -124.0881},
        "Redwood NP SKUNK CABBAGE TRAIL": {"lat": 41.3252, "lng": -124.0552}
    },
    "SEQU": {
        "Sequoia NP ASH MOUNTAIN ENTRANCE (LANE 1)": {"lat": 36.4851, "lng": -118.8351},
        "Sequoia NP ASH MOUNTAIN ENTRANCE (LANE 2)": {"lat": 36.4851, "lng": -118.8351},
        "Sequoia NP LOOKOUT POINT": {"lat": 36.3325, "lng": -118.7512},
        "Sequoia NP LOST GROVE": {"lat": 36.6212, "lng": -118.8212},
        "Sequoia NP SOUTH FORK": {"lat": 36.3452, "lng": -118.7652}
    },
    "KICA": {
        "Kings Canyon NP BIG STUMP": {"lat": 36.7143, "lng": -118.9634},
        "Kings Canyon NP CEDAR GROVE": {"lat": 36.7865, "lng": -118.8250},
        "Kings Canyon NP LOST GROVE (S. BOUND)": {"lat": 36.6212, "lng": -118.8212}
    },
    "SAGU": {
        "Saguaro NP CAM-BOH PICNIC AREA ROAD": {"lat": 32.2852, "lng": -111.1952},
        "Saguaro NP GOLDEN GATE LANE 3": {"lat": 32.2521, "lng": -111.1652},
        "Saguaro NP GOLDEN GATE LANE 4": {"lat": 32.2521, "lng": -111.1652},
        "Saguaro NP GOLDEN GATE ROAD OUTBOUND": {"lat": 32.2521, "lng": -111.1652},
        "Saguaro NP HOHOKAM ROAD OUTBOUND": {"lat": 32.2852, "lng": -111.2052},
        "Saguaro NP JAVELINA": {"lat": 32.1852, "lng": -110.7952},
        "Saguaro NP KINNEY ROAD AT RED HILLS VC": {"lat": 32.2521, "lng": -111.1652},
        "Saguaro NP PICTURED ROCKS LANE 2": {"lat": 32.3152, "lng": -111.2352},
        "Saguaro NP PICTURED ROCKS LANE 5": {"lat": 32.3152, "lng": -111.2352},
        "Saguaro NP SANDARIO ROAD LANE 1": {"lat": 32.2852, "lng": -111.2152},
        "Saguaro NP SANDARIO ROAD LANE 2": {"lat": 32.2852, "lng": -111.2152},
        "Saguaro NP CACTUS DRIVE": {"lat": 32.1752, "lng": -110.7952}
    },
    "YOSE": {
        "Yosemite NP ARCH ROCK": {"lat": 37.6744, "lng": -119.7121},
        "Yosemite NP BADGER PASS": {"lat": 37.6621, "lng": -119.6652},
        "Yosemite NP BIG OAK FLAT": {"lat": 37.7997, "lng": -119.8805},
        "Yosemite NP BIG TREE": {"lat": 37.5021, "lng": -119.6352},
        "Yosemite NP HETCH HETCHY": {"lat": 37.9102, "lng": -119.7781},
        "Yosemite NP SOUTH ENTRANCE": {"lat": 37.5025, "lng": -119.6321},
        "Yosemite NP TIOGA PASS": {"lat": 37.9108, "lng": -119.2567}
    },
    "CRLA": {
        "Crater Lake NP ANNIE SPRINGS ENTRANCE": {"lat": 42.8711, "lng": -122.1381},
        "Crater Lake NP NORTH ENTRANCE": {"lat": 43.0852, "lng": -122.1052}
    },
    "MORA": {
        "Mount Rainier NP WHITE RIVER ENTRANCE": {"lat": 46.8997, "lng": -121.5528},
        "Mount Rainier NP CARBON RIVER ENTRANCE": {"lat": 46.9952, "lng": -121.9152},
        "Mount Rainier NP CAYUSE PASS (410 WEST)": {"lat": 46.8682, "lng": -121.5382},
        "Mount Rainier NP MATHER WYE (410 EAST)": {"lat": 46.8952, "lng": -121.5521},
        "Mount Rainier NP NISQUALLY ENTRANCE": {"lat": 46.7410, "lng": -121.9167},
        "Mount Rainier NP OHANAPECOSH (123 NORTH)": {"lat": 46.7352, "lng": -121.4852},
        "Mount Rainier NP PAUL PEAK TRAILHEAD": {"lat": 46.9652, "lng": -121.9052}
    },
    "NOCA": {
        "North Cascades NP CASCADES RIVER ROAD ENTRANCE": {"lat": 48.5152, "lng": -121.4352}
    },
    "OLYM": {
        "Olympic NP DEER PARK (ENTRANCE LANE)": {"lat": 47.9152, "lng": -123.2652},
        "Olympic NP EAST BEACH ROAD (NORTHBOUND LANE)": {"lat": 48.0752, "lng": -123.7552},
        "Olympic NP ENTRANCE LANE TO ELWHA": {"lat": 48.0121, "lng": -123.5852},
        "Olympic NP ENTRANCE TO RUBY BEACH PARKING AREA": {"lat": 47.7121, "lng": -124.4152},
        "Olympic NP EXIT LANE AT STAIRCASE RANGER STATION (HOODSPORT)": {"lat": 47.5136, "lng": -123.3289},
        "Olympic NP FEE COLLECTION STATION (HURRICANE)": {"lat": 48.0011, "lng": -123.4244},
        "Olympic NP HIGHWAY 101 (WESTBOUND LANE)": {"lat": 48.0152, "lng": -123.4352},
        "Olympic NP HOH ENTRANCE STATION (ENTRANCE LANE)": {"lat": 47.8597, "lng": -124.2694},
        "Olympic NP MORA ENTRANCE ROAD": {"lat": 47.9252, "lng": -124.5852},
        "Olympic NP NORTH SHORE ROAD (EASTBOUND LANE)": {"lat": 47.5552, "lng": -123.8821},
        "Olympic NP NORTHSHORE ROAD (ENTRANCE LANE)": {"lat": 47.5552, "lng": -123.8821},
        "Olympic NP OZETTE RNGR STATION": {"lat": 48.1521, "lng": -124.6652},
        "Olympic NP QUEETS": {"lat": 47.5452, "lng": -124.3121},
        "Olympic NP SOLEDUCK ROAD (NORTHBOUND LANE)": {"lat": 48.0686, "lng": -123.9458},
        "Olympic NP SOUTHSHORE ROAD (ENTRANCE LANE)": {"lat": 47.5052, "lng": -123.8921},
        "Olympic NP DOSEWALLIPS": {"lat": 47.6852, "lng": -123.1012}
    },
    "DENA": {
        "Denali NP & PRES MAIN ENTRANCE": {"lat": 63.7291, "lng": -148.8852}
    },
    "KATM": {
        "Katmai NP & PRES LAKE CAMP": {"lat": 58.6752, "lng": -156.6521}
    },
    "KEFJ": {
        "Kenai Fjords NP EXIT GLACIER": {"lat": 60.1852, "lng": -149.6321}
    }
}

LOCATION_NAME_PREFIXES = [
    'TRAFFIC COUNT AT',
    'TRAFFIC  COUNT AT',
    'TRAFFIC COUNT ON',
    'TRAFFIC COUNT ADJ',
    'TRAFFIC COUNT FROM',
    'TRAFFIC AT',
    'ADJ TRAFFIC COUNT',
    'ADJUSTED TRAFFIC COUNT',
]

LOCATION_NAME_SUFFIX_BLOCKLIST = [
    '(NO DATA PRIOR',
    'PRE 2010 WAS',
]

LOCATION_NAME_BLOCKLIST = [
    '(PRE 2010)',
    'EFFECTIVE 2010',
    'NUMBER OF VEHICLES AT',
    'TRAFFIC COUNT',
    '(ESTIMATED)',
    '(INFO ONLY)',
]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutException, WebDriverException)),
    before_sleep=lambda retry_state: print(f"Retrying {retry_state.fn.__name__} due to timeout...", file=sys.stderr)
)
def get_nps_traffic_data(park_code="YOSE"):
    # Configure Headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    url = f"https://irma.nps.gov/Stats/SSRSReports/Park%20Specific%20Reports/Traffic%20Counts?Park={park_code}"
    results = {}

    try:
        driver.get(url)
        
        print(f"Processing {park_code}", file=sys.stderr)

        driver.switch_to.frame(0)
        
        wait = WebDriverWait(driver, 20)
        wait.until(EC.element_to_be_clickable((By.ID, "ReportViewer_ctl04_ctl00")))
        rows = driver.find_elements(By.XPATH, "//td[contains(@id, 'oReportCell')]//tr[not(.//table)]")

        park_name = driver.find_element(By.XPATH, "//select[@id='ReportViewer_ctl04_ctl03_ddValue']/option[@selected='selected']").text
        
        location_name = None
        coords = None
        for row in rows:
            if row.find_elements(By.XPATH, ".//td[@colspan='13']"):
                heading = row.text.strip().upper()

                # Heading / location name parsing
                location_name = heading
                match = re.match('TRAFFIC COUNT \((.*)\)', location_name)
                if match:
                    location_name = match.group(1)
                for s in LOCATION_NAME_PREFIXES:
                    if s in location_name:
                        location_name = location_name.split(s)[1].strip()
                        break
                for s in LOCATION_NAME_SUFFIX_BLOCKLIST:
                    if s in location_name:
                        i = location_name.find(s)
                        location_name = location_name[:i].strip()
                for s in LOCATION_NAME_BLOCKLIST:
                    if s in location_name:
                        location_name = location_name.replace(s, '')
                        break
                location_name = location_name.strip()

                coords = NPS_TRAFFIC_LOCATIONS[park_code][f"{park_name} {location_name}"]
                print(park_code, park_name, location_name, coords, file=sys.stderr)
                continue

            cols = row.find_elements(By.CSS_SELECTOR, "td")
            if len(cols) != 15: continue
            if location_name is None: continue

            key = f"{park_name} {location_name}"
            year = cols[0].text.strip()

            if key not in results:
                results[key] = {
                    'lat': coords['lat'],
                    'lng': coords['lng'],
                    'counts': {},
                }
            
            counts = []
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            for idx, month in enumerate(months):
                count_raw = cols[idx + 1].text.replace(',', '').strip()
                counts.append(int(count_raw) if count_raw.isdigit() else 0)
            results[key]['counts'][year] = counts
    finally:
        driver.quit()
    return results

data = {
    'type': 'FeatureCollection',
    'features': [],
}
for park_code, locations in list(NPS_TRAFFIC_LOCATIONS.items()):
    results = get_nps_traffic_data(park_code)
    data['features'].extend([{
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [vals['lat'], vals['lng']]
        },
        'properties': {
            'park_code': park_code,
            'location': key,
            'counts': vals['counts']
        }
    } for key, vals in results.items()])

print(json.dumps(data, indent=2))
