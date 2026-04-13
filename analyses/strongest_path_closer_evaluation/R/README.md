# R Functions Directory

This directory contains modular R functions extracted from the main analysis notebook to improve code organization and reusability.

## File Organization

### `utils.R`
General utility functions used across the analysis:
- `load_or_execute()` - Check if cached file exists or execute code
- `colScale()` - Column-normalize a matrix
- `rowScale()` - Row-normalize a matrix
- `prefix_cols()` - Add prefix to dataframe column names
- `make_gradient()` - Create color gradient
- `get.body.ids()` - Get body IDs for a type string

### `data_processing.R`
Data fetching and processing functions:
- `fetch_connectivity()` - Fetch connectivity data with annotations
- `calculate_normed_adj_matrix()` - Calculate normalized adjacency matrix

### `path_analysis.R`
Neural path finding and analysis functions:
- `add_valence_flag()` - Add valence flag based on neurotransmitter
- `find_k_strongest_paths()` - Find k strongest paths using shortest path algorithm
- `find_k_strongest_paths_yen()` - Find k strongest paths using Yen's algorithm
- `summarise_paths_all()` - Comprehensive path summarization with synapse strengths

### `visualization.R`
Plotting and visualization functions:
- `pie_data()` - Prepare data for pie charts
- `pie_plot()` - Create pie chart visualization
- `clean_legend_names()` - Clean legend names in plots
- `plot_modality_pair()` - Plot modality pair comparisons
- `plot_modality_pair_4th()` - Plot modality pair comparisons (4th order)

### `neuroglancer.R`
Neuroglancer URL generation and shortening:
- `make_mcns_scene()` - Build MCNS scene for neuroglancer
- `make_ng_url()` - Make long Clio-NG URL from scene
- `shorten_free()` - Free URL shortener via is.gd
- `mcns_shortlink()` - Convenience wrapper: IDs to short Clio link
- `mcns_shortlink_groups()` - Create shortlinks for groups of IDs

## Usage

In the main R Markdown file, these functions are loaded via:

```r
source("R/utils.R")
source("R/data_processing.R")
source("R/path_analysis.R")
source("R/visualization.R")
source("R/neuroglancer.R")
```

## Benefits of This Organization

1. **Clarity**: Functions are grouped by purpose, making it easier to find and understand code
2. **Reusability**: Functions can be easily sourced in other analysis scripts
3. **Maintainability**: Updating a function only requires editing one location
4. **Reduced duplication**: No more duplicate function definitions (like the neuroglancer functions that were defined twice)
5. **Better testing**: Functions can be tested independently
6. **Smaller main file**: The main Rmd file focuses on the analysis workflow rather than function definitions

## Notes

- Functions that were previously defined multiple times in the Rmd file (e.g., `make_mcns_scene`, `make_ng_url`) are now defined once in the appropriate R file
- The `colScale()` and `rowScale()` functions were previously defined inside `calculate_normed_adj_matrix()` and are now standalone utilities
- All functions retain their original functionality and parameters
