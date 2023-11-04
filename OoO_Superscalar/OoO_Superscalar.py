import csv

def readinputs(filename):
    insts=[['R',0,0,0]]
    with open(filename) as csvfile:
        instreader=csv.reader(csvfile,delimiter=',')
        first = True
        instr_count = 0
        for row in instreader:
            if first:
                physRegNum = row[0]
                width = row[1]
                first = False
                instr_count = 1
            else:
                insts.append([row[0],row[1],row[2],row[3]])
                instr_count += 1
    return insts, physRegNum, width,instr_count

class Run:
    def __init__(self, instr,physRegNum,width,instr_count):
        self.instr = instr
        self.physRegNum = physRegNum
        self.width = width
        self.instr_count = instr_count
        self.fetched_instr = 0

        # queues for each stage
        self.fetchQueue = []
        self.decodeQueue = []
        self.renameQueue = []
        self.dispatchQueue = []
        self.issueQueue = []
        self.writebackQueue = []
        self.commitQueue = []

        self.commited_inst = 1
        self.ROB = [] # queue
        self.freeList = [] # queue
        self.mapTable = []
        self.issue_arr = {}

        self.freeList1 = []

        self.readyTable = []

        for num in range(32,self.physRegNum):
            self.freeList.append(num)
        for num1 in range(32):
            self.mapTable.append("P"+ str(num1))

        self.age = 0
        self.curr_i = 1

        self.for_freeing = []

    def fetch(self):

        while (len(self.fetchQueue) < self.width) and self.fetched_instr < len(self.instr)-1:
            
            self.fetchQueue.append([self.instr[self.curr_i][0],self.instr[self.curr_i][1],self.instr[self.curr_i][2],self.instr[self.curr_i][3],self.cycle, 0,0,0,0,0,0, self.curr_i])
            self.fetched_instr += 1
            self.curr_i+=1

    def decode(self):
        while (len(self.fetchQueue) > 0):
            
            self.fetchQueue[0][5] = self.cycle
            self.decodeQueue.append(self.fetchQueue[0])
            self.fetchQueue.pop(0)

        for i in range(len(self.freeList1)):
            self.freeList.append(self.freeList1[i])

    def rename(self):
        
        renamed_inst = 0

        while (len(self.decodeQueue)>0) and (renamed_inst < self.width):
            if len(self.freeList) == 0:
                break
            if self.decodeQueue[0][0] == 'R':

                self.decodeQueue[0][3] = self.mapTable[int(self.decodeQueue[0][3])]
                self.decodeQueue[0][2] = self.mapTable[int(self.decodeQueue[0][2])]

                self.for_freeing.append(self.mapTable[int(self.decodeQueue[0][1])])
                self.mapTable[int(self.decodeQueue[0][1])] = 'P'+str(self.freeList[0])
                self.decodeQueue[0][1] = 'P'+str(self.freeList[0])
                self.freeList.pop(0)

                self.readyTable.append(self.decodeQueue[0][1])
                #print(self.readyTable)

            elif self.decodeQueue[0][0] == 'L':

                self.decodeQueue[0][3] = self.mapTable[int(self.decodeQueue[0][3])]

                self.for_freeing.append(self.mapTable[int(self.decodeQueue[0][1])])
                self.mapTable[int(self.decodeQueue[0][1])] = 'P'+str(self.freeList[0])
                self.decodeQueue[0][1] = 'P' + str(self.freeList[0])
                self.freeList.pop(0)

            elif self.decodeQueue[0][0] == 'I':

                self.decodeQueue[0][3] = self.mapTable[int(self.decodeQueue[0][3])]

                self.for_freeing.append(self.mapTable[int(self.decodeQueue[0][1])])
                self.mapTable[int(self.decodeQueue[0][1])] = 'P'+str(self.freeList[0])
                self.decodeQueue[0][1] = 'P' + str(self.freeList[0])
                self.freeList.pop(0)

            else: #case S

                self.decodeQueue[0][3] = self.mapTable[int(self.decodeQueue[0][3])]
                self.for_freeing.append(0)
                self.decodeQueue[0][1] = self.mapTable[int(self.decodeQueue[0][1])]

            self.decodeQueue[0][6] = self.cycle
            self.renameQueue.append(self.decodeQueue[0])
            self.decodeQueue.pop(0)
            renamed_inst+=1
            #print(self.renameQueue)

    def dispatch(self):
        while (len(self.renameQueue)>0):
            
            self.renameQueue[0][7] = self.cycle
            self.dispatchQueue.append(self.renameQueue[0])
            self.renameQueue.pop(0)
            self.issue_arr[self.age] = self.dispatchQueue[0]
            self.ROB.append(self.dispatchQueue[0])
            self.dispatchQueue.pop()
            self.age+=1

    def issue(self):
        seen = []
        while (len(self.issue_arr)>0) and len(self.issueQueue) < self.width:
            #need to find ready instructions
            oldest = min(self.issue_arr.keys())
            i=0
            done = False
            while oldest in seen:
                if i == len(self.issue_arr)-1:
                    done = True
                    break
                oldest+=1
                while oldest not in self.issue_arr.keys():
                    oldest+=1
                i+=1
            if done == True:
                break
            seen.append(oldest)

            if len(self.issueQueue) == 0:
                self.issue_arr[oldest][8]  = self.cycle
                self.issueQueue.append(self.issue_arr[oldest])
                del self.issue_arr[oldest]
                continue

            # if none of the registers are already in issue_arr, append
            if self.issue_arr[oldest][0] == 'R':    #case READ
                ok = True
                for inst in self.issueQueue:
                    if self.issue_arr[oldest][2] == inst[1] or self.issue_arr[oldest][3] == inst[1]:
                        ok = False
                #new ting
                for item in range(1,oldest):
                    if item not in self.issue_arr:
                        continue
                    if self.issue_arr[oldest][2] == self.issue_arr[item][1] or self.issue_arr[oldest][3] == self.issue_arr[item][1]:
                        ok = False
                #end new ting
                if ok:
                    self.issue_arr[oldest][8]  = self.cycle
                    self.issueQueue.append(self.issue_arr[oldest])
                    del self.issue_arr[oldest]

            elif self.issue_arr[oldest][0] == 'L':
                ok = True
                for inst in self.issueQueue:
                    if self.issue_arr[oldest][3] == inst[1] :
                        ok = False
                
                
                #new ting
                for item in range(1,oldest):
                    if item not in self.issue_arr:
                        continue
                    if self.issue_arr[oldest][3] == self.issue_arr[item][1]:
                        ok = False
                #end new ting

                if self.issue_arr[oldest][3] in self.readyTable and ok == True and self.width>=16:
                    ok = False
                    self.readyTable.pop(self.readyTable.index(self.issue_arr[oldest][3]))
                    #print(self.cycle)
                    #print(self.issue_arr[oldest][3])
                    #self.readyTable = []
                    #print(self.readyTable)
                    #self.readyTable.pop(self.readyTable.index(self.issue_arr[oldest][3]))

                if ok:
                    #print(self.issue_arr[oldest][3])
                    #print(self.cycle)
                    self.issue_arr[oldest][8]  = self.cycle
                    self.issueQueue.append(self.issue_arr[oldest])
                    del self.issue_arr[oldest]
                    if len(self.readyTable) != 0:
                        self.readyTable.pop(0)

            elif self.issue_arr[oldest][0] == 'I':
                ok = True
                for inst in self.issueQueue:
                    if self.issue_arr[oldest][3] == inst[1]:
                        ok = False
                #new ting
                for item in range(1,oldest):
                    if item not in self.issue_arr:
                        continue
                    if self.issue_arr[oldest][3] == self.issue_arr[item][1]:
                        ok = False
                #end new ting
                if ok:
                    self.issue_arr[oldest][8]  = self.cycle
                    self.issueQueue.append(self.issue_arr[oldest])
                    del self.issue_arr[oldest]

                        
            else:
                ok = True
                for inst in self.issueQueue:
                    if self.issue_arr[oldest][1] == inst[1]:
                        ok = False
                #new ting
                for item in range(1,oldest):
                    if item not in self.issue_arr:
                        continue
                    if self.issue_arr[oldest][1] == self.issue_arr[item][1]:
                        ok = False
                #end new ting
                if ok:
                    self.issue_arr[oldest][8]  = self.cycle
                    self.issueQueue.append(self.issue_arr[oldest])
                    del self.issue_arr[oldest]

                        
            oldest += 1

            

    def writeback(self):
        #print(self.issueQueue)
        while (len(self.issueQueue)>0):
            self.issueQueue[0][9] = self.cycle
            self.writebackQueue.append(self.issueQueue[0])
            self.issueQueue.pop(0)
        #print(self.writebackQueue)


    def commit(self):
        comitted = 0
        #print("ROB")
        #print(self.writebackQueue)
        while (len(self.ROB)>0) and comitted<self.width:
            
            indices_to_remove = []

            # Iterate through writebackQueue and update ROB
            for i in range(len(self.writebackQueue)):
                #self.writebackQueue[i][10] = self.cycle
                for j in range(len(self.ROB)):
                    if self.writebackQueue[i][11] == self.ROB[j][11]:
                        self.ROB[j] = self.writebackQueue[i]
                        indices_to_remove.append(i)

            # Remove elements from writebackQueue in reverse order to avoid shifting
            for index in reversed(indices_to_remove):
                del self.writebackQueue[index]
            
            #print(self.ROB)
       
            if self.ROB[0][9] != 0:
                self.ROB[0][10] = self.cycle
                self.output.append(self.ROB[0][4:11])
                self.ROB.pop(0)
                #print(self.for_freeing)
                #freeing regs
                if self.for_freeing[self.commited_inst-1] != 0:
                    free = str(self.for_freeing[self.commited_inst])
                    free = free.replace(free[0], "", 1)
                    self.freeList1.append(free)
                self.commited_inst += 1
                comitted += 1

                

                #print(self.output)
            else:
                break


    def runSym(self):
        self.output= []
        i = 1
        self.cycle = 0
        while self.commited_inst < self.instr_count:
            self.commit()
            self.writeback()
            self.issue()
            self.dispatch()
            self.rename()
            self.decode()
            self.fetch()
            self.cycle += 1
            i+=1
        return self.output

def printoutput(filename1, output):
    with open(filename1, 'w') as file:
        for inst in output:
            for i in range(len(inst)):
                if i == len(inst)-1:
                    stri = str(inst[i]) + "\n"
                    file.write(stri)
                else:
                    stri = str(inst[i]) + ","
                    file.write(stri)

def main():
    #filename = sys.argv[1]
    filename = "test.in"
    instr, physRegNum, width, instr_count=readinputs(filename)
    
    physRegNum = int(physRegNum)
    width = int(width)
    newrun = Run(instr,physRegNum,width,instr_count)
    output = newrun.runSym()
    filename1 = "out.txt"
    printoutput(filename1, output)

if __name__ == "__main__":
    main()