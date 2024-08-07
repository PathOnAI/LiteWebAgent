from multiprocessing import Pool
from browsergym_agent import use_agent_from_driver

if __name__ == '__main__':
    with Pool(processes=3) as pool:
        pool.map(use_agent_from_driver, [
            ["(1) search llama 3.1, (2) click google search, (3) click the 1st result"],
            ["(1) search llama 3.1, (2) click google search, (3) click the 2nd result"],
            ["(1) search llama 3.1, (2) click google search, (3) click the 3rd result"],
        ])