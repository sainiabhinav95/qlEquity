import QuantLib as ql
import numpy as np
import matplotlib.pyplot as plt

print("QuantLib version: ", ql.__version__)

if __name__ == '__main__':
    # Set the evaluation date
    evaluation_date = ql.Date(14, 2, 2025)
    print(evaluation_date)
    
