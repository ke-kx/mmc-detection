from dmmc.dmmc import *


if __name__ == "__main__":
    import pickle
    filename = "android_ContextTypeLoader.pkl"

    with open("output/dmmc/" + filename, "rb") as input:
        results = pickle.load(input)

    print("--------------------------------------------------")
    print("Results for ", filename)

    print(results)
