import vrep
import math
import random
import time

# Define Individual class
class Individual:
    # Constructor
    def __init__(self, iteration):
        self.name = "Undividual_" + str(iteration)

        self.genes = []
        # For each individual, we give him 9 genes, 3 for each motor
        for i in range(0, 3):
            awrist = Gene(i, wristHandle, random.randint(0, 300))
            self.genes.append(awrist)

        for i in range(0, 3):
            aelbow = Gene(i, elbowHandle, random.randint(0, 300))
            self.genes.append(aelbow)

        for i in range(0, 3):
            ashoulder = Gene(i, shoulderHandle, random.randint(0, 300))
            self.genes.append(ashoulder)

        random.shuffle(self.genes)

    def __repr__(self):
        return"Individual {name: " + self.name + ", genes: " + str(self.genes) + '}'



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

        # Creating a population of 20 individuals
        populations = []

        # Creating each individual
        for i in range (0, 20):
            individual = Individual(i)
            populations.append(individual)

        #print populations

        for individual in populations:
            for gene in individual.genes:
                print "----- Simulation started -----"
                vrep.simxStartSimulation(clientID, opmode)

                vrep.simxSetJointTargetPosition(clientID, gene.type, math.radians(gene.action), opmode)
                vrep.simxSetJointTargetPosition(clientID, gene.type, math.radians(gene.action), opmode)
                vrep.simxSetJointTargetPosition(clientID, gene.type, math.radians(gene.action), opmode)

                # Wait in order to let the motors finish their movements
                # Tip: there must be a more efficient way to do it...
                time.sleep(5)

                vrep.simxStopSimulation(clientID, opmode)
                time.sleep(1)
                print "----- Simulation ended -----"

    # Close the connection to V-REP remote server
    # http://www.coppeliarobotics.com/helpFiles/en/remoteApiFunctionsPython.htm#simxFinish
    vrep.simxFinish(clientID)
else:
    print ('Failed connecting to remote API server')
print ('End')
