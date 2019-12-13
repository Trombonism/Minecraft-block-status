

from twisted.internet import reactor, defer
from quarry.net.client import ClientFactory, SpawningClientProtocol
from quarry.net.auth import ProfileCLI
import minecraft_data  # library housing conversions of Minecraft IDs to plaintext
import math

mcd = minecraft_data("1.13.2")


class ChunkProtocol(SpawningClientProtocol):

    def packet_chunk_data(self, buff):
        # Create dictionary mapping from block states to block names

        count = 0
        blockList = {}
        x, z, full = buff.unpack('ii?')
        bitmask = buff.unpack_varint()
        # heightmap = buff.unpack_nbt()  # added in 1.14
        sections, biomes = unpack_chunk(buff, bitmask)
        if (x + 1) * 16 < self.x or (z + 1) * 16 < self.z:
            block_entities = [buff.unpack_nbt() for _ in range(buff.unpack_varint())]
            return
        states = {}
        for i in mcd.blocks:
            index = mcd.blocks[i]
            name = index['name']
            min = index['minStateId']
            max = index['maxStateId']
            if min == max:
                states[min] = name
            else:
                for x in range(min, max + 1):
                    states[x] = name
        startrealx = (x * 16)
        startrealz = (z * 16)
        realx = startrealx
        realz = startrealz
        realy = 0
        for i in sections:
            if i is None:
                break
            for j in i[0]:
                block = states[j]
                if realx == self.x and realy == self.y and realz == self.z:
                    print(block)
                    print("State: " + str(j))
                    self.close()
                    reactor.callFromThread(reactor.stop)

                if block not in blockList:
                    blockList[block] = 1
                else:
                    blockList[block] = blockList[block] + 1
                count = count+1
                realx = realx + 1
                if realx == startrealx + 16:
                    realx = startrealx
                    realz = realz + 1
                if realz == startrealz + 16:
                    realz = startrealz
                    realy = realy + 1
        #     print(count)
        # print(blockList)
        # print("x: " + str(x*16) + ", z: " + str(z*16))

        block_entities = [buff.unpack_nbt() for _ in range(buff.unpack_varint())]

    def addCoordinates(self, x, y, z):
        self.x = int(x)
        self.y = int(y)
        self.z = int(z)


# Unpacks data regarding blocks in the chunk from the supplied buffer
# A slightly modified version is necessary here as the function included in the Quarry library did not function properly
def unpack_chunk(self, bitmask, full=True, overworld=True):
    size = self.unpack_varint()
    sections = []
    for idx in range(16):
        if bitmask & (1 << idx):
            section = self.unpack_chunk_section()
        else:
            section = None
        sections.append(section)
    if full:
        biomes = self.unpack('I' * 256)
    else:
        biomes = None
    return sections, biomes


class ChunkFactory(ClientFactory):
    protocol = ChunkProtocol

    def transferCoor(self, xcoor, ycoor, zcoor):
        self.protocol.addCoordinates(self.protocol, xcoor, ycoor, zcoor)



@defer.inlineCallbacks
def run(args, xcoor, ycoor, zcoor):
    # Log in
    profile = yield ProfileCLI.make_profile(args)

    # Create factory
    factory = ChunkFactory(profile)
    factory.transferCoor(xcoor, ycoor, zcoor)

    # Connect!
    factory.connect(args.host, args.port)


def main(argv):
    parser = ProfileCLI.make_parser()
    parser.add_argument("host")
    parser.add_argument("-p", "--port", default=25565, type=int)
    args = parser.parse_args(argv)

    xcoor = input("Enter x coordinate: ")
    ycoor = input("Enter y coordinate: ")
    zcoor = input("Enter z coordinate: ")

    run(args, xcoor, ycoor, zcoor)

    reactor.run()

if __name__ == "__main__":
    import sys
    main(sys.argv[1:])