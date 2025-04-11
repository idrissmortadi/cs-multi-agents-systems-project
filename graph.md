flowchart TD
    %% Main process nodes
    start([🤖 Agent Activation]) --> comm
    
    %% Communication process section
    subgraph Communication["Communication Processes"]
        comm{{📡 Communication Hub}}
        comm -->|"Update Memory"| waste_detect[/"🔍 Waste Detection: Agents report waste locations"/]
        comm -->|"Share Targets"| waste_assign[/"🎯 Waste Assignment: Agents share their targets"/]
    end
    
    %% Decision process
    subgraph Decision["Decision Making"]
        waste_detect --> check[("📋 Check available waste in collective memory")]
        waste_assign --> check
        check --> decision{{"❓ Is waste available in memory?"}}
    end
    
    %% Waste searching path
    subgraph Search["Search Operations"]
        decision -->|"No"| search["🔎 Search Strategy: Move randomly/with heuristic scanning for waste"] 
        style search fill:#f9d77e,stroke:#d4b256,stroke-width:2px
        search --> found{{"🔍 Found new waste?"}}
        style found fill:#ffcccc,stroke:#ff9999,stroke-width:2px
        found -->|"No"| continue["🔄 Continue searching"]
        style continue fill:#f9d77e,stroke:#d4b256,stroke-width:2px
        continue --> search
        found -->|"Yes"| report["📢 Report to collective memory"]
        style report fill:#a3d977,stroke:#82c756,stroke-width:2px
    end
    
    %% Waste collection path
    subgraph Collection["Collection Process"]
        decision -->|"Yes"| assign["✅ Assign waste to self"]
        style assign fill:#a3d977,stroke:#82c756,stroke-width:2px
        report --> assign
        assign --> collect["🔄 Collect assigned waste"]
        style collect fill:#77c2d9,stroke:#56a0b8,stroke-width:2px
        collect --> report_pickup["📢 Report pickup to memory (remove from available wastes)"]
        style report_pickup fill:#a3d977,stroke:#82c756,stroke-width:2px
    end
    
    %% Processing path
    subgraph Processing["Processing Operations"]
        report_pickup --> count{{"❓ Collected 2 waste items?"}}
        style count fill:#ffcccc,stroke:#ff9999,stroke-width:2px
        count -->|"No"| check
        count -->|"Yes"| transform["⚙️ Transform waste to next type for yellow and green wastes"]
        style transform fill:#d977c2,stroke:#b856a0,stroke-width:2px
        transform --> report_transform["📢 Report transformation to memory with position"]
        style report_transform fill:#a3d977,stroke:#82c756,stroke-width:2px
    end
    
    %% Delivery path
    subgraph Delivery["Delivery Operations"]
        report_transform --> dropoff["🚚 Transport to transfer/drop zone"]
        style dropoff fill:#d9a377,stroke:#b88256,stroke-width:2px
        dropoff --> report_drop["📢 Report drop to memory with position"]
        style report_drop fill:#a3d977,stroke:#82c756,stroke-width:2px
        report_drop --> start
    end
    
    %% Style for subgraphs
    classDef subgraphStyle fill:#f0f8ff,stroke:#4682b4,stroke-width:2px
    class Communication,Decision,Search,Collection,Processing,Delivery subgraphStyle
    
    %% Node styles
    style start fill:#d0f0c0,stroke:#6b8e23,stroke-width:2px
    style comm fill:#c9daf8,stroke:#4285f4,stroke-width:2px
    style decision fill:#ffcccc,stroke:#ff9999,stroke-width:2px
    style check fill:#f0f0f0,stroke:#999999,stroke-width:2px
    style waste_detect fill:#f9e79f,stroke:#f39c12,stroke-width:2px
    style waste_assign fill:#f9e79f,stroke:#f39c12,stroke-width:2px