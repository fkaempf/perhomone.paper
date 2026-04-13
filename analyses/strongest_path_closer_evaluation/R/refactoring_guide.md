# Refactoring Guide

## Summary

This analysis file has been refactored to extract reusable functions into separate R source files in the `R/` directory. This improves code organization, reduces duplication, and makes the main analysis file more readable.

## What Changed

### 1. New Directory Structure
```
strongest.path.closer.evaluation/
├── R/
│   ├── README.md                  # Documentation of all functions
│   ├── utils.R                    # General utility functions
│   ├── data_processing.R          # Data fetching and processing
│   ├── path_analysis.R            # Path finding algorithms
│   ├── visualization.R            # Plotting functions
│   └── neuroglancer.R             # Neuroglancer URL generation
├── strongest.path.closer.evaluation.Rmd
└── ...
```

### 2. Functions Extracted

The following functions have been moved to external R files:

**From `utils.R`:**
- load_or_execute()
- colScale()
- rowScale()
- prefix_cols()
- make_gradient()
- get.body.ids()

**From `data_processing.R`:**
- fetch_connectivity()
- calculate_normed_adj_matrix()

**From `path_analysis.R`:**
- add_valence_flag()
- find_k_strongest_paths()
- find_k_strongest_paths_yen()
- summarise_paths_all()

**From `visualization.R`:**
- pie_data()
- pie_plot()
- clean_legend_names()
- plot_modality_pair()
- plot_modality_pair_4th()

**From `neuroglancer.R`:**
- make_mcns_scene()
- make_ng_url()
- shorten_free()
- mcns_shortlink()
- mcns_shortlink_groups()

### 3. Duplicate Functions Removed

The following functions were defined multiple times in the original file and are now defined once:
- `make_mcns_scene()` - was defined at lines 4456 and 4662
- `make_ng_url()` - was defined at lines 4598 and 4843
- `shorten_free()` - was defined at lines 4618 and 4863
- `mcns_shortlink()` - was defined at lines 4629 and 4874
- `plot_modality_pair()` - was defined at lines 5302 and 5642
- `colScale()` and `rowScale()` - were defined inside calculate_normed_adj_matrix()

## Instructions for Using the Refactored Code

### Option 1: Keep Original Function Definitions (Safest)
If you want to keep the original code working without any changes, you can:
1. Keep all the original function definitions in the Rmd file as they are
2. Simply add the source() statements (already added) to load the external versions
3. The external versions will override the inline versions when both exist

### Option 2: Comment Out Original Definitions (Cleaner)
To make the file cleaner and avoid duplication:
1. Comment out the function definition chunks (they are already commented in some sections)
2. Keep only the source() statements in the setup chunk
3. The analysis code will use the functions from the R/ files

### Option 3: Remove Original Definitions Completely (Cleanest)
For the cleanest approach:
1. Remove all the commented function definitions
2. Keep only the source() statements
3. Rely entirely on the R/ files for function definitions

## Testing the Refactored Code

To verify everything works correctly:

1. Clear your R environment
2. Run the Rmd file from the beginning
3. All functions should load from the R/ directory
4. All analysis chunks should execute without errors

If you encounter any issues:
- Check that all source() paths are correct
- Verify that the R/ directory is in the correct location relative to the Rmd file
- Ensure all required libraries are loaded before sourcing the R files

## Benefits

- **No more duplicate functions**: Each function is defined in exactly one place
- **Better organization**: Functions are grouped by purpose
- **Easier maintenance**: Update a function once, use it everywhere
- **Reusability**: Functions can be sourced in other scripts
- **Cleaner main file**: The Rmd file focuses on the analysis workflow
- **Better documentation**: Each R file can have its own documentation
