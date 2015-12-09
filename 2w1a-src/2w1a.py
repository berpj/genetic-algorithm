import vrep
import math
import copy
import random
import time

### Socket.io client ###
from socketIO_client import SocketIO, BaseNamespace
import jsonpickle

class Namespace(BaseNamespace):

    def on_connect(self):
        print('[Connected] to server socket.io')

    def on_disconnect(self):
        print('[Disconnected] to server socket.io')

socketIO = SocketIO('localhost', 5000, Namespace)

raw_input("Press Enter to continue when the client is launched...")

########################

POPIND = 80 # Nbr d'individu par population
BESTIND = int(POPIND / 4) # Nbr d'individu garde a la fin des selections
NBGENE = 15 # Multiple de trois
MUTATE = 5 # Chiffre compris entre 0 et 100 nombre d'individus concerne par la mutation dans une population en pourcentage
GMUTATE = 30 # Chiffre compris entre 0 et 100 nombre de genes concerne par la mutation dans un individu en pourcentage
MINMOTOR = 0
MAXMOTOR = 300
GENMAX = 500 # Nombre de generation maximum
GENEPERGEN = 6 # Nombre de genes ajoutes a chaque generation (multiple de 3)

# Define Individual class
class Individual:
    # Constructor
    def __init__(self, iteration):
        self.name = "Individual_" + str(iteration)
        self.generation = 0
        self.distance = 0
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
        self.distance = distance
    
    def getDistance(self):
        return self.distance

    def setScore(self, score):
        self.score = score
    
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
        return "Gene {name: " + self.name + ', type: ' + str(self.type) + ', degree: '+ str(self.action) + '}'



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
    ret4, leftWheelHandle = vrep.simxGetObjectHandle(clientID, "LeftWheelJoint", opmode)
    ret5, rightWheelHandle = vrep.simxGetObjectHandle(clientID, "RightWheelJoint", opmode)

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
        
        maxIndScore = 0
        # New generation
        for gen in range(0, GENMAX):
            print "Génération " + str(gen)

            # Send data to dashboard
            socketIO.emit('start_generation', gen);

            print "Number of gene for this population: " + str(NBGENE)
            popMaxScore = 0 # Score maximum par génération
            for individual in population1:

                print "----- Evaluation of "+ individual.name +"started -----"
                vrep.simxStartSimulation(clientID, opmode)
                theTime = time.time()
                # Start getting the robot position
                pret, robotPos = vrep.simxGetObjectPosition(clientID, robotHandle, -1, vrep.simx_opmode_streaming)
                pret4, leftWheelPos = vrep.simxGetObjectPosition(clientID, leftWheelHandle, -1, vrep.simx_opmode_streaming)
                pret5, rightWheelPos = vrep.simxGetObjectPosition(clientID, rightWheelHandle, -1, vrep.simx_opmode_streaming)
                print "2w1a position: (x = " + str(robotPos[0]) + ", y = " + str(robotPos[1]) + ")"
                # Start getting the robot orientation
                oret, robotOrient = vrep.simxGetObjectOrientation(clientID, robotHandle, -1, vrep.simx_opmode_streaming)

                print "2w1a orientation: (x = " + str(robotOrient[0]) + \
                      ", y = " + str(robotOrient[1]) +\
                      ", z = " + str(robotOrient[2]) + ")"
                for gene in individual.genes:
                    vrep.simxSetJointTargetPosition(clientID, gene.type, math.radians(gene.action), opmode)
                    pgene = vrep.simxGetJointPosition(clientID, gene.type, opmode)
                    #time.sleep(0.05)
                    # Wait in order to let the motors finish their movements

                    # timer = time.time()
                    # while True:
                        # pgene = vrep.simxGetJointPosition(clientID, gene.type, opmode)

                        # if round(math.degrees(pgene[1]), 0) == round(gene.action, 0):
                            # break
                        # else:
                            # time.sleep(0.01)
                        # timer += 0.01

                        # if time.time() >= timer + 3:
                            # theTime = 0
                            # break

                    # if theTime == 0:
                        # break

                oret, robotOrientEnd = vrep.simxGetObjectOrientation(clientID, robotHandle, -1, vrep.simx_opmode_streaming)
                pret, robotPosEnd = vrep.simxGetObjectPosition(clientID, robotHandle, -1, vrep.simx_opmode_streaming)

                pret4, leftWheelPosEnd = vrep.simxGetObjectPosition(clientID, leftWheelHandle, -1, vrep.simx_opmode_streaming)
                pret5, rightWheelPosEnd = vrep.simxGetObjectPosition(clientID, rightWheelHandle, -1, vrep.simx_opmode_streaming)
                
                individual.setDistance(math.sqrt(math.pow(math.degrees(robotPosEnd[0]) - math.degrees(robotPos[0]),2) + math.pow(math.degrees(robotPosEnd[1]) - math.degrees(robotPos[1]),2)))
                theTime = time.time() - theTime
                # Set the score by distance between start x & y and end x & y
                individual.setScore(int(individual.getDistance()))
                # Set the score by the stability of robot
                if leftWheelPosEnd[2] > rightWheelPosEnd[2] + 0.02 or leftWheelPosEnd[2] > leftWheelPos[2] + 0.02 or rightWheelPosEnd[2] > rightWheelPos[2] + 0.02:
                    individual.setScore(int(individual.score / 100))
                else:
                    # Set the score by the direction the robot take
                    print "Z score: " + str(math.degrees(robotOrientEnd[2]))
                    individual.setScore(int(individual.getScore() / (180*(math.fabs(robotOrientEnd[2])+0.01)/100)))
                print "Distance parcourue: " + str(individual.getDistance())
                print "Score obtenu: " + str(individual.getScore())
                scoreTotal = scoreTotal + individual.getScore()

                # Send data to dashboard
                socketIO.emit('simulation_end', jsonpickle.encode([gen, individual.getScore(), individual]));

                vrep.simxStopSimulation(clientID, opmode)
                time.sleep(0.2)
                if individual.getScore() > popMaxScore :
                    popMaxScore = individual.getScore()
                if individual.getScore() > maxIndScore :
                    maxIndScore = individual.getScore()
                    print "maxIndScore => " + str(maxIndScore)
                print "----- Evaluation ended -----"

            # Send data to dashboard
            socketIO.emit('new_generation', jsonpickle.encode([gen, population1 + population2]));

            if (gen > 0 and populations[0].score <= maxIndScore and gen % 6 == 1):
                NBGENE = NBGENE + GENEPERGEN
            populations = population1 + population2
            print "----- Sélection par roulette -----"
            selection = []
            population2 = populations
            for i in range(0, BESTIND):
                random.shuffle(population2)
                scoreToReach = random.randint(0, int(scoreTotal))
                tmpScore = 0
                for individu in population2:
                    tmpScore = tmpScore + int(individu.getScore())
                    if (tmpScore >= scoreToReach):
                        selection.append(individu)
                        scoreTotal = scoreTotal - individu.getScore()
                        population2.remove(individu)
                        break
            print "pop length: " + str(len(populations))
            print "----- Fin de la selection -----"
            print "----- Supression des individus faibles -----"
            populations.sort(key=lambda individu: individu.score, reverse=True)
            if (len(populations) > POPIND):
                lenOfPop = int(len(populations)/2)
                for i in range(0, lenOfPop):
                    scoreTotal = scoreTotal - populations[-1].getScore()
                    populations.pop();
            print "pop length after death: " + str(len(populations))
            population2 = populations
            print "----- Début du croisement -----"
            population1 = []
            for i in range(0, POPIND):
                individual = Individual(i)
                for g in range(0, NBGENE/3):
                    selLen = len(selection)
                    breed = selection[random.randint(0,selLen-1)]
                    breedpos = g * (len(breed.genes) / 3);
                    individual.setGene(Gene(g*3, wristHandle, breed.getGene(breedpos%len(breed.genes)).action))
                    individual.setGene(Gene(g*3+1, elbowHandle, breed.getGene(breedpos%len(breed.genes)+1).action))
                    individual.setGene(Gene(g*3+2, shoulderHandle, breed.getGene(breedpos%len(breed.genes)+2).action))
                population1.append(individual)
            print "Résultat du croisement: " + str(population1)
            print "----- Fin du croisement -----"
            print "----- Mutation started -----"

            for i in range (0, int((POPIND * MUTATE) / 100)):
                individual = population1[i]
                for i2 in range (0, int((NBGENE * GMUTATE) / 100)):
                    prevGene = random.randint(0, NBGENE-1)
                    individual.genes[prevGene].action = random.randint(MINMOTOR, MAXMOTOR)

            print "----- End of mutation -----"
            print "Meilleur score de la génération actuelle: " + str(popMaxScore)
    print "Le score maximal de ces génération aura été de :" + str(maxIndScore)
    # Close the connection to V-REP remote server
    # http://www.coppeliarobotics.com/helpFiles/en/remoteApiFunctionsPython.htm#simxFinish
    vrep.simxFinish(clientID)
else:
    print ('Failed connecting to remote API server')
print ('End')
