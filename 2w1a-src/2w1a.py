import vrep
import math
import random
import time

POPIND = 20 # Nbr d'individu par population
BESTIND = int(POPIND / 4) # Nbr d'individu garde a la fin des selections
NBGENE = 9 # Multiple de trois
MUTATE = 50 # Chiffre compris entre 0 et 100 nombre d'individus concerne par la mutation dans une population en pourcentage
GMUTATE = 30 # Chiffre compris entre 0 et 100 nombre de genes concerne par la mutation dans un individu en pourcentage
MINMOTOR = 0
MAXMOTOR = 300
GENMAX = 20 # Nombre de generation maximum


# Define Individual class
class Individual:
    # Constructor
    def __init__(self, iteration):
        self.name = "Individual_" + str(iteration)
        self.generation = 0
        self.maxDistance = 0
        self.score = 0

        self.genes = []

    def __repr__(self):
        return"Individual {name: " + self.name + ", score: " + str(self.score) + '}'

    def setGene(self, gene):
        self.genes.append(gene)

    def addGene(self, type):
        self.genes.append(Gene(len(self.genes), type, random.randint(MINMOTOR, MAXMOTOR)))

    def getGene(self, nbr):
        return self.genes[nbr]

    def setDistance(self, distance):
        self.maxDistance = distance
    
    def getDistance(self):
        return self.maxDistance

    def setScore(self, score):
        self.score = score * 10000
    
    def getScore(self):
        return self.score


# Define Gene class
class Gene:
    # Constructor
    def __init__(self, iteration, type, action):
        self.name = "Gene_" + str(iteration)
        self.type = type
        self.action = action

    def __repr__(self):
        return "Gene {name: " + self.name + ', type: ' + str(self.type) + '}'



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

    vrep.simxStartSimulation(clientID, opmode)
    vrep.simxStopSimulation(clientID, opmode)

    # Try to retrieve motors and robot handlers
    # http://www.coppeliarobotics.com/helpFiles/en/remoteApiFunctionsPython.htm#simxGetObjectHandle
    ret1, wristHandle = vrep.simxGetObjectHandle(clientID, "WristMotor", opmode)
    ret2, elbowHandle = vrep.simxGetObjectHandle(clientID, "ElbowMotor", opmode)
    ret3, shoulderHandle = vrep.simxGetObjectHandle(clientID, "ShoulderMotor", opmode)

    ret4, robotHandle = vrep.simxGetObjectHandle(clientID, "2W1A", opmode)
    scoreTotal = 0

    # If handlers are OK, execute three random simulations
    if ret1 == 0 and ret2 == 0 and ret3 == 0:

        # Creating two population of 20 individuals
        population1 = []
        population2 = []

        # Creating each individual
        for i in range (0, POPIND):
            individual = Individual(i)
            # For each individual, we give him 9 genes, 3 for each motor
            for y in range (0, NBGENE / 3):
                individual.addGene(wristHandle)
                individual.addGene(elbowHandle)
                individual.addGene(shoulderHandle)
            population1.append(individual)
        
        # New generation
        for gen in range(0, GENMAX):

            for individual in population1:

                print "----- Evaluation started -----"
                vrep.simxStartSimulation(clientID, opmode)
                theTime = time.time()
                pret, robotPos = vrep.simxGetObjectPosition(clientID, robotHandle, -1, vrep.simx_opmode_streaming)
                print "2w1a position: (x = " + str(robotPos[0]) + ", y = " + str(robotPos[1]) + ")"

                for gene in individual.genes:

                    vrep.simxSetJointTargetPosition(clientID, gene.type, math.radians(gene.action), opmode)
                    pgene = vrep.simxGetJointPosition(clientID, gene.type, opmode)
                    print "Motor " + str(gene.type) + " reached position: " + str(gene.action) + " degree"

                    # Wait in order to let the motors finish their movements

                    timer = 0.0
                    while True:
                        pgene = vrep.simxGetJointPosition(clientID, gene.type, opmode)

                        if round(math.degrees(pgene[1]), 0) == round(gene.action, 0):
                            break
                        else:
                            time.sleep(0.01)
                        timer += 0.01

                        if timer >= 3.0:
                            theTime = 0
                            break

                pret, robotPosEnd = vrep.simxGetObjectPosition(clientID, robotHandle, -1, vrep.simx_opmode_streaming)
                print "2w1a position: (x = " + str(robotPosEnd[0]) + ", y = " + str(robotPosEnd[1]) + ")"
                individual.setDistance(math.sqrt(math.pow(robotPosEnd[0] - robotPos[0],2) + math.pow(robotPosEnd[1] - robotPos[1],2)))
                theTime = time.time() - theTime
                individual.setScore(individual.getDistance() / theTime)
                print "Distance parcourue: " + str(individual.getDistance())
                print "Score obtenu: " + str(individual.getScore())
                scoreTotal = scoreTotal + individual.getScore()
                vrep.simxStopSimulation(clientID, opmode)
                print "----- Evaluation ended -----"
            populations = population1 + population2
            print "----- Selection par roulette -----"
            selection = []
            for i in range(0, BESTIND):
                random.shuffle(populations)
                scoreToReach = random.randint(0, int(scoreTotal))
                tmpScore = 0
                for individu in populations:
                    tmpScore = tmpScore + int(individu.getScore())
                    if (tmpScore >= scoreToReach):
                        selection.append(individu)
                        scoreTotal = scoreTotal - individu.getScore()
                        populations.remove(individu)
                        break
            print "Resultat selection: " + str(selection)
            print "----- Fin de la selection -----"
            print "----- Supression des individus faibles -----"
            sorted(populations, key=lambda individu: individu.score)
            if (len(populations) > POPIND):
                lenOfPop = int(len(populations)/2)
                for i in range(0, lenOfPop):
                    scoreTotal = scoreTotal - populations[-1].getScore()
                    populations.pop()
            population2 = populations
            print "Old generation: " + str(population2)
            print "----- Debut du croisement -----"
            population1 = []
            for i in range(0, POPIND):
                individual = Individual(i)
                for g in range(0, NBGENE/3):
                    selLen = len(selection)
                    breed = selection[random.randint(0,selLen-1)]
                    individual.setGene(Gene(g*3, wristHandle, breed.getGene((g*(NBGENE/3)))))
                    individual.setGene(Gene(g*3+1, elbowHandle, breed.getGene((g*(NBGENE/3))+1)))
                    individual.setGene(Gene(g*3+2, shoulderHandle, breed.getGene((g*(NBGENE/3))+2)))
                population1.append(individual)
            print "Resultat du croisement: " + str(population1)
            print "----- Fin du croisement -----"
            print "----- Mutation started -----"

            for i in range (0, (POPIND * MUTATE) / 100):
                individual = population1[i]
                for i2 in range (0, (NBGENE * GMUTATE) / 100):
                    individual.genes[i].action = random.randint(MINMOTOR, MAXMOTOR)

            print "----- End of mutation -----"
    # Close the connection to V-REP remote server
    # http://www.coppeliarobotics.com/helpFiles/en/remoteApiFunctionsPython.htm#simxFinish
    vrep.simxFinish(clientID)
else:
    print ('Failed connecting to remote API server')
print ('End')
