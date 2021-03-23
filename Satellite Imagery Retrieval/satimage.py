import sys
from PIL import Image
import math
import urllib.request
import io

# lat and lon inputs
# IIT  -> 41.83964812674144 -87.63023269626457 41.830951000359796 -87.62313020670366
# Navy Pier -> 41.89678685333488 -87.6149592897909 41.888969652558636 -87.59796214342683
# Downtown -> 41.89345870872397 -87.63436202604326 41.87846740210062 -87.61159090214575

# calculations and convertions of (lat, lon), xy, quadkey are specified in https://docs.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system
MIN_LATITUDE, MAX_LATITUDE = (-85.05112878, 85.05112878) # square aspect ratio so instead of 90, its about 85.05 for bing tile system
MIN_LONGITUDE, MAX_LONGITUDE = (-180, 180)
MAX_SIZE = 4096 # set limit on size as some levels are too big -- level 5 is 8192 x 8192 and level 6 is twice that ..
# 8192 sometimes result in existing connection was forcibly closed by the remote host when getting image

def get_image(tileX, tileY, level, verbose = False):
    """
    Converts tile xy to quadkey
    Using the quadkey, downloads the image file
    """

    quadKey = ""
    for i in range(level, 0, -1):
        digit = '0'
        mask = 1 << (i - 1)
        if ((tileX & mask) != 0):
            digit = chr(ord(digit) + 1)
        if ((tileY & mask) != 0):
            digit = chr(ord(digit) + 2)
        quadKey += digit
    
    # ex. http://h0.ortho.tiles.virtualearth.net/tiles/h023131022213211200.jpeg?g=131
    make_url = lambda qkey: "http://h0.ortho.tiles.virtualearth.net/tiles/h" + qkey + ".jpeg?g=131"

    # get image
    imageURL = make_url(quadKey)
    if verbose:
        print(tileX, tileY, ":", imageURL)
    with urllib.request.urlopen(imageURL, timeout = 60) as response:
        image = Image.open(io.BytesIO(response.read()))
    
    return image

def to_pixel(lat, lon, level):
    """
    Converts latitude and longitude to pixel xy coordinates given level of detail
    """

    clip = lambda n, minValue, maxValue: min(max(n, minValue), maxValue)
    lat = clip(lat, MIN_LATITUDE, MAX_LATITUDE)
    lon = clip(lon, MIN_LONGITUDE, MAX_LONGITUDE)

    x = (lon + 180) / 360
    sinLatitude = math.sin(lat * (math.pi / 180))
    y = 0.5 - math.log((1 + sinLatitude) / (1 - sinLatitude)) / (4 * math.pi)

    mapSize = 256 << level
    pixelX = int(clip(x * mapSize + 0.5, 0, mapSize - 1))
    pixelY = int(clip(y * mapSize + 0.5, 0, mapSize - 1))

    return pixelX, pixelY

def create_image(tileX1, tileY1, tileX2, tileY2, level, userInput):
    """
    Iterates through tiles and downloads the image
    Combine the downloaded images and crop to user specified bounding box
    """

    # init image
    width = (tileX2 - tileX1 + 1) * 256
    height = (tileY2 - tileY1 + 1) * 256
    finalImage = Image.new('RGB', (width, height))

    # 'stitch' tiles
    for x in range(tileX1, tileX2 + 1):
        for y in range(tileY1, tileY2 + 1):
            image = get_image(x, y, level)
            x1 = int((x - tileX1) * 256)
            y1 = int((y - tileY1) * 256)

            finalImage.paste(image, (x1, y1, x1 + 256, y1 + 256))
    
    # crop image based on lat,lon input
    lat1, lon1 = userInput[0][0], userInput[0][1]
    lat2, lon2 = userInput[1][0], userInput[1][1]

    startX = tileX1 * 256
    startY = tileY1 * 256
    # xy of input
    ix1, iy1 = to_pixel(lat1, lon1, level)
    ix2, iy2 = to_pixel(lat2, lon2, level)

    finalX1 = ix1 - startX
    finalY1 = iy1 - startY
    finalX2 = ix2 - startX
    finalY2 = iy2 - startY

    finalImage = finalImage.crop((finalX1, finalY1, finalX2, finalY2))

    return finalImage


def to_tile(lat, lon, level):
    """
    Convert lat, lon to pixel xy coordinate based on level and then to tile xy
    """

    clip = lambda n, minValue, maxValue: min(max(n, minValue), maxValue)
    lat = clip(lat, MIN_LATITUDE, MAX_LATITUDE)
    lon = clip(lon, MIN_LONGITUDE, MAX_LONGITUDE)

    x = (lon + 180) / 360
    sinLatitude = math.sin(lat * (math.pi / 180))
    y = 0.5 - math.log((1 + sinLatitude) / (1 - sinLatitude)) / (4 * math.pi)

    mapSize = 256 << level
    pixelX = int(clip(x * mapSize + 0.5, 0, mapSize - 1))
    pixelY = int(clip(y * mapSize + 0.5, 0, mapSize - 1))

    # pixel to tile
    tileX = int(pixelX / 256)
    tileY = int(pixelY / 256)

    return tileX, tileY

def get_best_tiles(lat1, lon1, lat2, lon2):
    """
    Given bounding box with lat/lon input, gets tiles and also finds the best level of detail
    If a tile has no image, skips that level -- example of no iamge: http://h0.ortho.tiles.virtualearth.net/tiles/h13230312200111013112312.jpeg?g=131
    """

    # 23 level of details
    minLevel = 0
    for level in range(23, 0, -1):
        tileX1, tileY1 = to_tile(lat1, lon1, level)
        tileX2, tileY2 = to_tile(lat2, lon2, level)

        # make sure tiles are top left to bottom right
        if tileX1 > tileX2:
            tileX1, tileX2 = tileX2, tileX1
        if tileY1 > tileY2:
            tileY1, tileY2 = tileY2, tileY1

        # bounding box within same tile should be lowest level of detail
        if (tileX2 - tileX1 <= 1) and (tileY2 - tileY1 <= 1):
            minLevel = level
    
            currentLevel = 23
            while currentLevel >= minLevel: # top to bottom to get best
                good = True
                tileX1, tileY1 = to_tile(lat1, lon1, currentLevel)
                tileX2, tileY2 = to_tile(lat2, lon2, currentLevel)

                # make sure tiles are top left to bottom right
                if tileX1 > tileX2:
                    tileX1, tileX2 = tileX2, tileX1
                if tileY1 > tileY2:
                    tileY1, tileY2 = tileY2, tileY1

                # over 4096
                if (tileX2 - tileX1) * 256 > MAX_SIZE:
                    currentLevel -= 1
                    continue

                # skip if there no image- example: http://h0.ortho.tiles.virtualearth.net/tiles/h13230312200111013112312.jpeg?g=131
                for x in range(tileX1, tileX2 + 1):
                    for y in range(tileY1, tileY2 + 1):
                        image = get_image(x, y, currentLevel)
                        if image == Image.open("NO_IMAGE.png"):
                            good = False
                            print("No image at Tile", x, y, "at level", currentLevel)
                            break
                    if not good:
                        break
                #print(currentLevel, good)
                if good:
                    break

                currentLevel -= 1

            bestLevel = currentLevel
            #print(bestLevel, "best")
            if good:
                return tileX1, tileY1, tileX2, tileY2, bestLevel
    
    # should only go to here if all levels have at least 1 no image
    print("Unable to get image due to each level having an unavailable image in a tile inside the bounding box input")


if __name__ == "__main__":
    lat1, lon1 = float(sys.argv[1]), float(sys.argv[2])
    lat2, lon2 = float(sys.argv[3]), float(sys.argv[4])
    image_name = sys.argv[5]
    #print(sys.argv[0])

    # determining the tiles and best level of detail
    tileX1, tileY1, tileX2, tileY2, level = get_best_tiles(lat1, lon1, lat2, lon2)
    print(f"Got the tiles. ({tileX1}, {tileY1}) to ({tileX2}, {tileY2}) with level", level)

    # create image using tiles
    print("Creating image..")
    image = create_image(tileX1, tileY1, tileX2, tileY2, level, ((lat1, lon1), (lat2, lon2)))
    print(f"Created Image as {image_name}.png")

    image.save(f"{image_name}.png")

