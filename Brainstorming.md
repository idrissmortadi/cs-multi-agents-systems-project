Strategy : 

- Communication for waste detection : Agents update collective memory with waste locations.
- Communication for waste assignment : Agents share their assigned waste locations (strategies for assignements).

 
                   Check available waste to collect from collective memory 
                              /                         \    

                  If waste is available                If no waste available   
                              |                              |
                              |                              Move randomly / with heuristic 
                                                          scanning available waste (not in memory)
                      Assign it to yourself
                      and go collect it 