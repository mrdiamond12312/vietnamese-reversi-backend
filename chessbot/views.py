from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
# Create your views here.


@csrf_exempt
def getMove(request):
    from math import inf
    import copy
    # import sys

    weight = [[1, 1, 3, 1, 1],
              [1, 7, 4, 7, 1],
              [3, 4, 8, 4, 3],
              [1, 7, 4, 7, 1],
              [1, 1, 3, 1, 1]]

    starting_move = []

    # Some Pre-Calculated for moves
    encodedBoardHelper = [
        [(0, 0), (1, 0), (2, 0), (1, 0), (0, 1)],
        [(1, 3), (4, 0), (3, 0), (4, 0), (1, 1)],
        [(2, 3), (3, 0), (4, 0), (3, 0), (2, 1)],
        [(1, 3), (4, 0), (3, 0), (4, 0), (1, 1)],
        [(0, 3), (1, 2), (2, 2), (1, 2), (0, 2)]
    ]

    directValue = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1), (0, 0), (0, 1),
        (1, -1), (1, 0), (1, 1)
    ]

    boardDirect = [
        [[5, 8, 7], [7, 6, 3], [3, 0, 1], [1, 2, 5]],
        [[5, 7, 3], [7, 3, 1], [3, 1, 5], [1, 5, 7]],
        [[5, 7, 3, 8, 6], [7, 3, 1, 6, 0], [3, 1, 5, 0, 2], [1, 5, 7, 2, 8]],
        [[1, 3, 5, 7]],
        [[0, 1, 2, 3, 5, 6, 7, 8]]
    ]

    symmetricPoint = [
        [[], [], [], []],
        [[(5, 3)], [(7, 1)], [(3, 5)], [(1, 7)]],
        [[(5, 3)], [(7, 1)], [(3, 5)], [(1, 7)]],
        [[(3, 5), (1, 7)]],
        [[(0, 8), (1, 7), (3, 5), (2, 6)]]
    ]

    boardHelper = []
    '''List of available destinations of a possition'''
    symmetricHelper = []
    for i in range(5):
        boardHelper.append([])
        symmetricHelper.append([])
        for j in range(5):
            helper = encodedBoardHelper[i][j]
            indexes = boardDirect[helper[0]][helper[1]]
            directs = [directValue[x] for x in indexes]
            xy = [(x[0]+i, x[1]+j) for x in directs]
            symIndexes = symmetricPoint[helper[0]][helper[1]]
            symmetrics = [(directValue[x[0]], directValue[x[1]])
                          for x in symIndexes]
            symXy = [[(x[0]+i, x[1]+j) for x in y] for y in symmetrics]
            boardHelper[i].append(xy)
            symmetricHelper[i].append(symXy)

    def checkValidMove(move) -> bool:
        '''Check if we can move from move[0] to move[1]'''
        (fx, fy) = move[0]
        (tx, ty) = move[1]
        if ((tx, ty) in boardHelper[fx][fy]):
            return True
        else:
            return False

    def moveChessman(board, move):
        '''Move that piece'''
        fx, fy = move[0]
        tx, ty = move[1]
        (board[tx][ty], board[fx][fy]) = (board[fx][fy], board[tx][ty])

    def getBoardAfterMove(board, player, pos):
        (x, y) = pos
        unvisit = list.copy(boardHelper[x][y])
        isEaten = False
        # Get "Gánh" chessmans
        isEaten |= _eatBySymmetries(board, player, pos, unvisit)
        # Get "Vây" chessmans
        liberty_map = _liberty(board)
        for i, row in enumerate(liberty_map):
            for j, col in enumerate(row):
                if board[i][j] != 0 and col == False:
                    board[i][j] = player
                    isEaten |= True

        for i in range(5):
            for j in range(5):
                visitted = set()
                chessPlayer = board[i][j]
                if (chessPlayer != 0 and chessPlayer != player
                    and not _getUnmoveChessList(board, chessPlayer,
                                                (i, j), visitted)):

                    for changePos in visitted:
                        (px, py) = changePos
                        board[px][py] = player
                        isEaten |= True
        return isEaten

    def _getUnmoveChessList(board, curChessPlayer, pos, visitted):
        if pos in visitted:
            return False
        visitted.add(pos)
        (x, y) = pos
        helper = boardHelper[x][y]
        rt = False
        i = 0
        n = len(helper)
        while i < n and not rt:
            (px, py) = helper[i]
            chessPlayer = board[px][py]
            if chessPlayer == 0:
                rt = rt or True
            elif chessPlayer == curChessPlayer:
                rt = rt or _getUnmoveChessList(
                    board, curChessPlayer, helper[i], visitted)
            i += 1
        return rt

    def _eatBySymmetries(board, player, pos, unvisit):
        isEaten = False
        (x, y) = pos
        symmetries = symmetricHelper[x][y]
        for sym in symmetries:
            (x1, y1) = sym[0]
            (x2, y2) = sym[1]
            chess1Player = board[x1][y1]
            chess2Player = board[x2][y2]
            if chess1Player == 0 or chess2Player == 0:
                if chess1Player == 0 and sym[0] in unvisit:
                    unvisit.remove(sym[0])
                if chess2Player == 0 and sym[1] in unvisit:
                    unvisit.remove(sym[1])
                continue
            if chess1Player == chess2Player:
                if player != chess1Player:
                    isEaten |= True
                    board[x1][y1] = player
                    board[x2][y2] = player
                    unvisit.remove(sym[0])
                    unvisit.remove(sym[1])
        return isEaten

    def _liberty(board):
        liberty_map = [[False]*5 for i in range(5)]
        for i, row in enumerate(board):
            for j, pos in enumerate(row):
                if pos != 0:
                    # First get piece of chess with liberty (air)
                    surrounding = boardHelper[i][j]
                    if any(board[place[0]][place[1]] == 0 for place in surrounding):
                        liberty_map[i][j] = True

        # Check for group liberty:
        while (True):
            changed = False
            for i, row in enumerate(liberty_map):
                for j, pos in enumerate(row):
                    if board[i][j] != 0 and liberty_map[i][j] == False:
                        surrounding = boardHelper[i][j]
                        if any(liberty_map[place[0]][place[1]] == True and board[place[0]][place[1]] == board[i][j] for place in surrounding):
                            liberty_map[i][j] = True
                            changed = True
            if changed == False:
                break
        return liberty_map

    def isTrapChess(board, fromPos, toPos):
        (fx, fy) = fromPos
        (tx, ty) = toPos
        symmetries = symmetricHelper[fx][fy]
        player = board[tx][ty]
        # check every symmetries
        for sym in symmetries:
            if (board[sym[0][0]][sym[0][1]] == board[sym[1][0]][sym[1][1]] == player):
                helper = boardHelper[fx][fy]
                for point in helper:
                    (px, py) = point
                    if board[px][py] == -player:
                        return True
        return False

    def getMovableChessList(board, player, trapPos=None):
        movableList = []
        # Get trapped piece if exist
        if trapPos is not None:
            (trX, trY) = trapPos
            helper = boardHelper[trX][trY]
            for point in helper:
                (px, py) = point
                chessPlayer = board[px][py]
                if player == chessPlayer:
                    movableList.append(point)
            if len(movableList) > 0:
                return movableList
        # Get all player chess
        for i in range(5):
            for j in range(5):
                if board[i][j] == player:
                    point = (i, j)
                    if isMovableChess(board, point):
                        movableList.append(point)
        return movableList

    def isMovableChess(board, chessPos):
        (x, y) = chessPos
        moveList = boardHelper[x][y]
        for point in moveList:
            (px, py) = point
            if board[px][py] == 0:
                return True
        return False

    def getMovablePositionList(board, pos, trapPos=None):
        movablePosList = []
        if trapPos is not None:
            movablePosList.append(trapPos)
        else:
            (x, y) = pos
            helper = boardHelper[x][y]
            for point in helper:
                (px, py) = point
                if board[px][py] == 0:
                    movablePosList.append(point)
        return movablePosList

    def eval(board, player):
        count_me = 0
        count_player = 0
        for i, row in enumerate(board):
            for j, pos in enumerate(row):
                if pos == player:
                    count_me += 10 + weight[i][j]
                elif pos == -player:
                    count_player += 10 + weight[i][j]
        return count_me - count_player

    def findPrevMove(prev_board, board):
        # initialize positions of a move
        fromPos = [0, 0]
        toPos = [0, 0]
        # flags when positions are found
        pFlag = True
        mFlag = True
        # search through 2 boards
        for i in range(5):
            for j in range(5):
                if (pFlag and prev_board[i][j] != 0 and board[i][j] == 0):
                    fromPos = tuple([i, j])
                    pFlag = False
                if (mFlag and prev_board[i][j] == 0 and board[i][j] != 0):
                    toPos = tuple([i, j])
                    mFlag = False
                if (not pFlag and not mFlag):
                    break
        return fromPos, toPos

    def calculateF(board):
        f = 0
        for row in board:
            for col in row:
                f += col
        return f

    def isFinished(board):
        f = calculateF(board)
        return f == 16 or f == -16

    def move(prev_board, board, player, remain_time_x, remain_time_o):
        depth = 3

        trap = None
        if (prev_board):
            if (calculateF(prev_board) == calculateF(board)):
                fromPos, toPos = findPrevMove(prev_board, board)
                if (isTrapChess(board, fromPos, toPos)):
                    trap = fromPos

        try:
            return tuple(minimax(board, trap, depth, player, True, -inf, inf, depth)[1])
        except:
            return (None)
        # if res is None:
        #     return (None)
        # return tuple(res)

    def minimax(board, trap, depth, player, maximizing, alpha, beta, max_depth):
        if isFinished(board):
            return -300 + (max_depth - depth)*2, None
        if depth == 0:
            return eval(board, player) - (max_depth - depth)*2, None
        if not maximizing:
            bestVal = -inf
            bestMove = None
            pieceList = getMovableChessList(board, player, trap)
            moves = []
            for piece in pieceList:
                for move in getMovablePositionList(board, piece, trap):
                    moves.append([piece, move])
            if not moves:
                return eval(board, player) - (max_depth - depth)*2, None
            else:
                for move in moves:
                    newBoard = copy.deepcopy(board)
                    moveChessman(newBoard, move)
                    isEaten = getBoardAfterMove(newBoard, player, move[1])
                    trap = None
                    if not isEaten:
                        if (isTrapChess(newBoard, move[0], move[1])):
                            trap = move[0]
                    value = minimax(newBoard, trap, depth - 1, -
                                    player, True, alpha, beta, max_depth)[0]
                    bestVal = max(bestVal, value)
                    if bestVal == value:
                        bestMove = move
                    alpha = max(alpha, bestVal)
                    if (beta <= alpha):
                        break

                return bestVal, bestMove
        else:
            bestVal = inf
            bestMove = None
            pieceList = getMovableChessList(board, player, trap)
            moves = []
            for piece in pieceList:
                for move in getMovablePositionList(board, piece, trap):
                    moves.append([piece, move])
            if not moves:
                return eval(board, player) - (max_depth - depth)*2, None
            else:
                for move in moves:
                    newBoard = copy.deepcopy(board)
                    moveChessman(newBoard, move)
                    isEaten = getBoardAfterMove(newBoard, player, move[1])
                    trap = None
                    if not isEaten:
                        if (isTrapChess(newBoard, move[0], move[1])):
                            trap = move[0]
                    value = minimax(newBoard, trap, depth - 1, -
                                    player, False, alpha, beta, max_depth)[0]
                    bestVal = min(bestVal, value)
                    if bestVal == value:
                        bestMove = move
                    beta = min(beta, bestVal)
                    if (beta <= alpha):
                        break

                return bestVal, bestMove

    reqBody = json.loads(request.body)

    result_move = move(
        reqBody.get('prevBoard'),
        reqBody.get('board'),
        reqBody.get('player'), 15, 15
    )

    return JsonResponse({
        'move':
        {
            'from': {'row': result_move[0][0], 'col': result_move[0][1]},
            'to': {'row': result_move[1][0], 'col': result_move[1][1]},
        }
    })
