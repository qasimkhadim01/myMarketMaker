import numpy as np

class AsyncCovarMatrixArray:
    def __int__(self, rows, covarEstFactory, *, synchFactory=None):
        self.rows = rows
        self.synchronizer = np.empty(shape=(rows))
        self.covarEst = np.empty(shape=(rows))
        self.covar = np.empty(shape=(rows, rows))

        for row in range(rows):
            self.synchronizer[row] = np.empty(shape=(row + 1))
            self.covarEst[row] = np.empty(shape=(row + 1))
            for col in range(rows):
                self.synchronizer[row][col] = LinearSynchronizer() if synchFactory == None else synchFactory.build()
                self.covarEst[row][col] = covarEstFactory.build()

    def update(self, indexToUpdate, timestamp, price):
        for row in range(self.rows):
            for col in range(self.rows):
                if row == indexToUpdate:
                    self.synchronizer[row][col].asyncUpdate(Side.Left, timestamp, price)
                    testSynchronizer(row, col, timestamp)
                if col == indexToUpdate:
                    self.synchronizer[row][col].asyncUpdate(Side.Right, timestamp, price)
                    testSynchronizer(row, col, timestamp)

    def testsynchronizer(self, row, col, timestamp):
        if self.synchronizer[row][col].isValid():
            covarUpdate = self.coverEst[row][col].update(timestamp
                                        ,self.synchronizer[row][col].getAsynchValues().getLeft()
                                        ,self.synchronizer[row][col].getAsynchValues().getRight())
            self.covar[row][col] = covarUpdate
            self.covar[col][row] = covarUpdate

    def getValue(self, row, col):
        return self.covar[row][col]

    def getCovarMatrix(self):
        return self.covar