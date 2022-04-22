from sumo.wrapper import SumoClient

sumo = SumoClient("dev", interactive=False)

result = sumo.get("/search", query="class:case", size=1, select=["_sumo"])
print(result)
