- Pick only your color 
- Once you pick up 2 wastes of your own color => transform them to color + 1  and move it to the drop zone

Refactor deliberate 

  - Check if you have 2 wastes of color => call "transform_waste"
        transform_waste : update the carried type + carried_amount
  - Check if you have 1 waste of color + 1 
  
    => call "move" ( args ? )
    => checking that you are in (color + 1) * (size/3) row the  "drop_waste"  

