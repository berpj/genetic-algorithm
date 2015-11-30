import vrep
import math
import random
import time

POPIND = 20 # Nbr d'individu par population
BESTIND = POPIND / 4 # Nbr d'individu garde a la fin des selections
NBGENE = 9 # Multiple de trois
MUTATE = 50 # Chiffre compris entre 0 et 100 nombre d'individus concerne par la mutation dans une population en pourcentage
GMUTATE = 30 # Chiffre compris entre 0 et 100 nombre de genes concerne par la mutation dans un individu en pourcentage
MINMOTOR = 0
MAXMOTOR = 300


# Define Individual class
class Individual:
    # Constructor
    def __init__(self, iteration):
        self.name = "Undividual_" + str(iteration)
        self.generation = 0
        self.maxDistance = 0

        self.genes = []

        random.shuffle(self.genes)

    def __repr__(self):
        return"Individual {name: " + self.name + ", genes: " + str(self.genes) + '}'

    def setGene(self, type, gene):
        for i in range(0, NBGENE):
            if self.genes[i].type == type:
                self.genes[i] = gene
        random.shuffle(self.genes)

    def beginGenesis(self, nb, type):
        for i in range(0, nb):
            self.genes.append(Gene(len(self.genes), type, random.randint(MINMOTOR, MAXMOTOR)))
        random.shuffle(self.genes)



# Define Gene class
class Gene:
    # Constructor
    def __init__(self, iteration, type, action):
        self.name = "Gene_" + str(iteration)
        self.type = type
        self.action = action

    def __repr__(self):
        return "Individual {name: " + self.name + ', type: ' + self.type + '}'



print ('Start')

# Close eventual old connections
vrep.simxFinish(-1)
# Connect to V-REP remote server
clientID = vrep.simxStart('127.0.0.1', 19997, True, True, 5000, 5)

if clientID != -1:
    print ('Connected to remote API server')

    # Communication operating mode with the remote API : wait for its answer before continuing (blocking mode)
    # http://www.coppeliarobotics.com/helpFiles/en/remoteApiConstants.htm
    opmode = vrep.simx_opmode_oneshot_wait

    # Try to retrieve motors and robot handlers
    # http://www.coppeliarobotics.com/helpFiles/en/remoteApiFunctionsPython.htm#simxGetObjectHandle
    ret1, wristHandle = vrep.simxGetObjectHandle(clientID, "WristMotor", opmode)
    ret2, elbowHandle = vrep.simxGetObjectHandle(clientID, "ElbowMotor", opmode)
    ret3, shoulderHandle = vrep.simxGetObjectHandle(clientID, "ShoulderMotor", opmode)

    ret4, robotHandle = vrep.simxGetObjectHandle(clientID, "2W1A", opmode)

    # If handlers are OK, execute three random simulations
    if ret1 == 0 and ret2 == 0 and ret3 == 0:

        # Creating two population of 20 individuals
        population1 = []
        population2 = []

        # Creating each individual
        for i in range (0, POPIND):
            individual = Individual(i)
            # For each individual, we give him 9 genes, 3 for each motor
            individual.beginGenesis(NBGENE / 3, wristHandle)
            individual.beginGenesis(NBGENE / 3, elbowHandle)
            individual.beginGenesis(NBGENE / 3, shoulderHandle)
            population1.append(individual)

        #print populations
        populations = population1 + population2

        for individual in populations:

            print "----- Simulation started -----"
            vrep.simxStartSimulation(clientID, opmode)
            pret, robotPos = vrep.simxGetObjectPosition(clientID, robotHandle, -1, vrep.simx_opmode_streaming)
            print "2w1a position: (x = " + str(robotPos[0]) + ", y = " + str(robotPos[1]) + ")"

            for gene in individual.genes:

                vrep.simxSetJointTargetPosition(clientID, gene.type, math.radians(gene.action), opmode)
                pgene = vrep.simxGetJointPosition(clientID, gene.type, opmode)
                print "Motor " + str(gene.type) + " reached position: " + str(gene.action) + " degree"
                # Wait in order to let the motors finish their movements
                # Tip: there must be a more efficient way to do it...
                time.sleep(3)

            pret, robotPosEnd = vrep.simxGetObjectPosition(clientID, robotHandle, -1, vrep.simx_opmode_streaming)
            print "2w1a position: (x = " + str(robotPosEnd[0]) + ", y = " + str(robotPosEnd[1]) + ")"
            print "Distance parcourue: " + str(math.sqrt(math.pow(robotPosEnd[0] - robotPos[0],2) + math.pow(robotPosEnd[1] - robotPos[1],2)))
            vrep.simxStopSimulation(clientID, opmode)
            print "----- Simulation ended -----"
            time.sleep(2)

    # Close the connection to V-REP remote server
    # http://www.coppeliarobotics.com/helpFiles/en/remoteApiFunctionsPython.htm#simxFinish
    vrep.simxFinish(clientID)
else:
    print ('Failed connecting to remote API server')
print ('End')
