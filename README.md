# Scissors-Paper-Rock Battlefield

A dynamic simulation of the classic Rock-Paper-Scissors game, reimagined as an ecosystem where three species compete for survival in a beautiful, Monet-inspired color palette.

## Features

### Core Mechanics
- **Three Species Ecosystem**: Scissors (Pink), Paper (Green), and Rock (Blue) dots compete in a circular arena
- **Natural Selection**: Each group can consume its prey while avoiding its predators
- **Real-time Status Display**: A live-updating table shows each group's population and relationships

### Strategic Behavior
- **Population Awareness**: Dots become strategic when:
  - Their prey population falls below critical levels
  - Predator population becomes threatening
  - Any group is near extinction
  - Population balance becomes delicate
- **Protective Behaviors**: 
  - Ultra-protective mode when prey species are endangered (<8 dots)
  - Defensive formations when populations are low
  - Active avoidance of last remaining prey
  - Circular movement patterns to maintain safe distances

### Dynamic Movement
- **Individual Speed Ranges**: Each dot has unique movement capabilities
  - Minimum speed: 0.1
  - Maximum speed: 1.2
  - Personalized speed range with at least 0.3 difference
- **Strategic Movement Patterns**:
  - Sideways movement to avoid confrontation
  - Center-seeking behavior when endangered
  - Random movement to break predictable patterns
  - Circular orbiting around prey groups

### Environmental Features
- **Shrinking Arena**: A gradually contracting boundary adds pressure to the ecosystem
- **Population Balance**: Groups self-regulate to maintain ecosystem stability
- **Visual Feedback**: 
  - Distinct shapes for each species (X, Square, Circle)
  - Status table showing current populations and relationships
  - Monet-inspired color palette for visual appeal

## Philosophy

The simulation explores several fascinating paradoxes of survival:

1. **The Predator's Dilemma**: 
   - Aggressive hunting may lead to prey extinction
   - Without prey, predators cannot survive
   - Strategic restraint becomes crucial for long-term survival

2. **Balance Through Chaos**:
   - Individual dots act independently
   - Collective behavior emerges from simple rules
   - Complex patterns form without central coordination

3. **Survival Strategies**:
   - Direct competition vs. strategic avoidance
   - Population awareness influences behavior
   - Self-regulation prevents ecosystem collapse

## Controls

- Launch the simulation by running `main.py`
- Watch as the ecosystem evolves and adapts
- Observe the status table for real-time population information
- The simulation will automatically restart when a winner emerges

## Requirements

- Python 3.x
- Pygame library

## Installation

1. Clone this repository
2. Install Pygame: `pip install pygame`
3. Run `main.py`

## Color Palette

- Scissors: Lily Pink (Inspired by Monet's Water Lilies)
- Paper: Leaf Green (From Monet's Garden scenes)
- Rock: Water Blue (Reflecting Monet's pond paintings)
- Background: Deep Blue (Evening atmosphere)
- Boundary: Soft Lavender (Misty garden edges)
- Highlights: Soft White (Morning light)
