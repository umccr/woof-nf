render_warning_files <- function(d.missing_files) {
  s.summary_text_templ <- '
  <summary>
    <span style="color: #e9c46a;">Missing <b>${length(v.files_missing)}</b> expected ${s.plurality}</span>
    <span style="color: #b0b0b0;">(click for details)</span>
  </summary>
  '
  v.files_missing <- d.missing_files$file
  s.plurality <- ifelse(length(v.files_missing) > 1, 'files', 'file')
  s.summary_text <- stringr::str_interp(s.summary_text_templ)

  cat('<details>', s.summary_text, '<div class="details-container">', sep='')
  cat(
    d.missing_files %>%
      knitr::kable(format='html') %>%
      kableExtra::kable_styling(full_width=FALSE, position='left')
  )
  cat('</div></details>', sep='')
}

# NOTE: currently only used once by the small variant PCGR variant table. If this remains true, remove as generalised fn
render_warning_variants <- function(d.display_data) {
  s.summary_text_templ <- '
  <summary>
    <span style="color: #e9c46a;">Not displaying <b>${n.variants_undisplayed}</b> ${s.plurality}</span>
    <span style="color: #b0b0b0;">(click for details)</span>
  </summary>
  '
  n.variants_undisplayed <- sum(d.display_data$`Not displayed`)
  s.plurality <- ifelse(n.variants_undisplayed > 1, 'variants', 'variant')
  s.summary_text <- stringr::str_interp(s.summary_text_templ)

  cat('<details>', s.summary_text, '<div class="details-container">', sep='')
  cat(
    d.display_data %>%
      knitr::kable(format='html') %>%
      kableExtra::kable_styling(full_width=FALSE, position='left')
  )
  cat('</div></details>', sep='')
}

# NOTE: see above re single usage
get_variant_display_data <- function(d.full, d.subset) {
  # Set columns and display names
  v.column_display_names <- c(
    'Sample name',
    'Displayed'='displayed',
    'Not displayed'='not_displayed',
    'Total'='total'
  )
  # For each sample, get count of total variants, displayed variants, and undisplayed variants
  # 1. count total variants
  # 2. count displayed variants
  # 3. bind rows and cast to wider format
  # 4. rename and order columns
  d.counts_full <- d.full %>%
    dplyr::group_by(`Sample name`) %>%
    dplyr::summarise(n=n()) %>%
    dplyr::mutate(type='total')
  d.counts_subset <- d.subset %>%
    dplyr::group_by(`Sample name`) %>%
    dplyr::summarise(n=n()) %>%
    dplyr::mutate(type='displayed')
  dplyr::bind_rows(
    d.counts_full,
    d.counts_subset,
  ) %>%
    tidyr::pivot_wider(names_from=type, values_from=n) %>%
    dplyr::mutate(not_displayed=total-displayed) %>%
    dplyr::select(tidyselect::all_of(v.column_display_names))
}
