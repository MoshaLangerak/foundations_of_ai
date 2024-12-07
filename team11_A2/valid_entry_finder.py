from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove

class ValidEntryFinder:

    def __init__(self,game_state: GameState):
        """
        Initialize attributes from the game_state object.
        @param game_state: GameState object representing the current state of the Competitive Sudoku game.
        """
        # initialize game_state object attributes
        self.board = game_state.board
        self.taboo_moves = game_state.taboo_moves

        # get all occupied squares
        self.occupied_squares = set(game_state.occupied_squares1) | set(game_state.occupied_squares2)

        # get the allowed squares attributes for the correct player and exclude the occupied squares
        # self.allowed_squares = (
        #     set(game_state.allowed_squares1) if game_state.current_player == 1 else set(game_state.allowed_squares2)
        # ) - self.occupied_squares
        self.allowed_squares = set(game_state.player_squares()) - self.occupied_squares

        # initialize board size # ! can maybe be optimized by using SudokuBoard class methods
        self.size = self.board.n * self.board.m
        self.n = self.board.n
        self.m = self.board.m


    def squares2values(self, squares: set) -> set:
        """
        Converts coordinates to values of entries in those coordinates.
        @param squares: set of coordinates that have to be converted to their values.
        @return: set of values that correspond to the set of coordinates given.
        """
        # return set(self.board.squares[self.board.square2index(sq)] for sq in squares) - {0}
        return set(self.board.get(sq) for sq in squares) - {0}


    def get_row_dict(self) -> dict:
        """
        Find all numbers (excluding 0) that are present in each allowed row.
        @return: dictionary with row numbers as keys and the numbers included in the corresponding rows as values
        """
        # get all unique row coordinates in allowed_squares
        allowed_row_coordinates = set(square[0] for square in self.allowed_squares)

        # fill dictionary with numbers per row
        dct_row_nrs = {}
        for row_coord in allowed_row_coordinates:
            # get coords of entire row with row coordinate
            row_coords = set((row_coord,i) for i in range(self.size))

            # assign current values of all squares in the row to dictionary (excluding 0/. as they are not valid entry options)
            dct_row_nrs[row_coord] = self.squares2values(row_coords)

        return dct_row_nrs
    

    def get_col_dict(self) -> dict:
        """
        Find all numbers (excluding 0) that are present in each allowed column.
        @return: dictionary with column numbers as keys and the numbers included in the corresponding columns as values.
        """
        # get all unique column coordinates in allowed_squares
        allowed_col_coordinates = set(square[1] for square in self.allowed_squares)

        # fill dictionary with numbers per column
        dct_col_nrs = {}
        for col_coord in allowed_col_coordinates:
            # get coords of entire column with column coordinate
            current_col_coords = set((i,col_coord) for i in range(self.size))

            # assign current values of all squares in the column to dictionary (excluding 0/. as they are not valid entry options)
            dct_col_nrs[col_coord] = self.squares2values(current_col_coords)

        return dct_col_nrs
    

    def get_block_id(self, coordinate: tuple) -> int:
        """
        Get the identifier the block within which coordinate lies
        @param coordinate: tuple of the format (row, column).
        @return: identifier of the block within which coordinate lies as an integer
        """
        return (coordinate[0]//self.m) * self.m + (coordinate[1]//self.n)
        
    def get_block_coordinates(self, block_id: int) -> set[tuple]: # ! set[tuple] used here, which is not as detailed in other functions
        """
        Find all coordinates of the block with block_id.
        @param block_id: identifier of the block of which the coordinates should be found.
        @return: set of all (n*m) coordinates inside the block with block_id.
        """
        # compute starting row and column of the block
        block_row_start = (block_id // self.m) * self.m
        block_col_start = (block_id % self.m) * self.n

        # generate all coordinates within the block
        coordinates = {
            (row, col)
            for row in range(block_row_start, block_row_start + self.m)
            for col in range(block_col_start, block_col_start + self.n)
        }

        return coordinates
    
    def get_block_dict(self) -> dict:
        """
        Find all numbers (excluding 0) that are present in each allowed block.
        @return: dictionary with block ids as keys and the numbers included in the corresponding blocks as values.
        """
        # get all unique block ids in allowed_squares
        allowed_block_ids = set(self.get_block_id(square) for square in self.allowed_squares)

        # fill dictionary with values per block
        dct_block_nrs = {}
        for block_id in allowed_block_ids:
            # get coords of all squares in the block
            current_block_coords = self.get_block_coordinates(block_id)
            # assign current values of all squares in the block to dictionary (excluding 0/. as they are not valid entry options)
            dct_block_nrs[block_id] = self.squares2values(current_block_coords)
        
        return dct_block_nrs

        
    def get_pos_entries(self) -> dict:
        """
        Find all possible entries for the allowed squares of the current player.
        @return: dictionary with the allowed squares as keys and the possible entries in the corresponding squares as values.
        """

        # get the available entries based on the board seize
        available_entries = set(range(1, self.size+1))
        
        # get dictionary for values in each row, column, and block
        dct_row_numbers = self.get_row_dict()
        dct_col_numbers = self.get_col_dict()
        dct_block_numbers = self.get_block_dict()

        # compute possible values for each (empty) square
        dct_pos_entries = {}
        for square in self.allowed_squares:
            row_values = dct_row_numbers[square[0]]
            col_values = dct_col_numbers[square[1]]
            block_values = dct_block_numbers[self.get_block_id(square)]

            # get the values that are not possible in the current square
            present_values = row_values | col_values | block_values

            if square == (2, 3):
                print("Checking taboo moves for square (2,3):")
                print(
                    f"Available entries before taboo check: {available_entries - present_values}")
                print(f"Taboo moves: {self.taboo_moves}")
                print(
                    f"Testing TabooMove((2,3), 1) in taboo_moves: {TabooMove((2,3), 1) in self.taboo_moves}")
            
            # compute possible entries
            pos_entries = set(
                entry for entry in (available_entries - present_values)
                if TabooMove(square, entry) not in self.taboo_moves
            )

            dct_pos_entries[square] = pos_entries
        
        return dct_pos_entries
