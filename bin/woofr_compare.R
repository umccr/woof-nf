#MIT License
#
#Copyright (c) 2019 Peter Diakumis
#
#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

library("dplyr")
library("purrr")
library("tibble")
library("tidyr")

#' Get bcbio final output files
#'
#' Generates a tibble containing absolute paths to bcbio final files.
#'
#' @param d Path to `<bcbio/final>` directory.
#' @return A tibble with the following columns:
#'   - vartype: variant type. Can be one of:
#'     - SNV (single-nucleotide/indel variants)
#'     - SV (structural variants)
#'   - flabel: file label (e.g. ensemble, manta, vardict etc.)
#'   - fpath: path to file
#'
#' @examples
#' \dontrun{
#' d <- "path/to/bcbio/final"
#' bcbio_outputs(d)
#' }
#' @export
bcbio_outputs <- function(d) {
  stopifnot(dir.exists(d))
  vcfs <- list.files(d, pattern = "\\.vcf.gz$", recursive = TRUE, full.names = TRUE)
  stopifnot(length(vcfs) > 0)

  tibble::tibble(fpath = vcfs) %>%
    dplyr::mutate(
      bname = sub("\\.vcf.gz$", "", basename(.data$fpath)),
      fpath = normalizePath(.data$fpath),
      flabel = dplyr::case_when(
        grepl("germline-ensemble", .data$bname) ~ "ens-germ_bc",
        grepl("ensemble", .data$bname) ~ "ens-batch_bc",
        grepl("germline-vardict", .data$bname) ~ "vardict-germ_bc",
        grepl("vardict-germline", .data$bname) ~ "vardict-germ2_bc",
        grepl("vardict", .data$bname) ~ "vardict-batch_bc",
        grepl("germline-strelka2", .data$bname) ~ "strelka2-germ_bc",
        grepl("strelka2", .data$bname) ~ "strelka2-batch_bc",
        grepl("mutect2", .data$bname) ~ "mutect2-batch_bc",
        grepl("germline-gatk-haplotype", .data$bname) ~ "gatk-germ_bc",
        grepl("germline-sv-prioritize-manta$", .data$bname) ~ "IGNORE_ME",
        grepl("germline-manta$", .data$bname) ~ "IGNORE_ME",
        grepl("sv-prioritize-manta$", .data$bname) ~ "IGNORE_ME",
        grepl("-manta$", .data$bname) ~ "manta_bc",
        TRUE ~ "IGNORE_ME"),
      vartype = dplyr::case_when(
        flabel == "IGNORE_ME" ~ "IGNORE_ME",
        flabel == "manta_bc" ~ "SV",
        TRUE ~ "SNV")) %>%
    dplyr::select(.data$vartype, .data$flabel, .data$fpath) %>%
    dplyr::distinct()
}

#' Gather bcbio filepaths from two bcbio final directories into a single tibble
#'
#' Generates a tibble containing absolute paths to (common) files from two bcbio final directories.
#'
#' @param d1 Path to first `<bcbio/final>` directory.
#' @param d2 Path to second `<bcbio/final>` directory.
#' @param sample Sample name.
#' @return A tibble with the following columns:
#'   - sample name
#'   - variant type (e.g. SNV, SV, CNV)
#'   - file label (e.g. ensemble, manta, vardict etc.)
#'   - run1 file path
#'   - run2 file path
#'
#' @examples
#' \dontrun{
#' final1 <- "path/to/bcbio/final1"
#' final2 <- "path/to/bcbio/final2"
#' merge_bcbio_outputs(final1, final2)
#' }
#' @export
merge_bcbio_outputs <- function(d1, d2, sample) {

  final1 <- bcbio_outputs(d1)
  final2 <- bcbio_outputs(d2)

  dplyr::inner_join(final1, final2, by = c("flabel", "vartype")) %>%
    dplyr::filter(!.data$vartype == "IGNORE_ME") %>%
    dplyr::mutate(sample_nm = sample) %>%
    dplyr::select(.data$sample_nm, .data$vartype, .data$flabel, .data$fpath.x, .data$fpath.y) %>%
    utils::write.table(file = "", quote = FALSE, sep = "\t", row.names = FALSE, col.names = FALSE)
}

#' Get umccrise final output files
#'
#' Generates a tibble containing absolute paths to umccrise final files.
#'
#' @param d Path to `<umccrised/sample>` umccrise directory.
#' @return A tibble with the following columns:
#'   - vartype: variant type. Can be one of:
#'     - SNV (single-nucleotide/indel variants)
#'     - SV (structural variants)
#'     - CNV (copy number variants)
#'   - flabel: file label (e.g. pcgr, cpsr, purple etc.)
#'   - fpath: path to file
#'
#' @examples
#' \dontrun{
#' um <- "path/to/umccrised/sample"
#' umccrise_outputs(um)
#' }
#' @export
umccrise_outputs <- function(d) {
  stopifnot(dir.exists(d))
  # grab PURPLE's purple.gene.cnv file too
  vcfs <- list.files(d, pattern = "\\.vcf.gz$", recursive = TRUE, full.names = TRUE)
  purple_cnv <- list.files(d, pattern = "purple.*gene", recursive = TRUE, full.names = TRUE)
  stopifnot(length(vcfs) > 0, length(purple_cnv) <= 1)
  all_files <- c(vcfs, purple_cnv)

  tibble::tibble(fpath = all_files) %>%
    dplyr::mutate(
      bname = sub("\\.vcf.gz$", "", basename(.data$fpath)),
      fpath = normalizePath(.data$fpath),
      flabel = dplyr::case_when(
        grepl("-somatic-ensemble-PASS$", .data$bname) ~ "pcgr_um",
        grepl("-normal-ensemble-predispose_genes$", .data$bname) ~ "cpsr_um",
        grepl("manta$", .data$bname) ~ "manta_um",
        grepl("purple.*gene", .data$bname) ~ "purple-gene_um",
        TRUE ~ "IGNORE_ME"),
      vartype = dplyr::case_when(
        flabel == "IGNORE_ME" ~ "IGNORE_ME",
        flabel == "manta_um" ~ "SV",
        flabel == "purple-gene_um" ~ "CNV",
        flabel %in% c("pcgr_um", "cpsr_um") ~ "SNV",
        TRUE ~ "IGNORE_ME")) %>%
    dplyr::select(.data$vartype, .data$flabel, .data$fpath)
}

#' Gather umccrise filepaths from two umccrise final directories into a single tibble
#'
#' Generates a tibble containing absolute paths to (common) files from two umccrise final directories.
#'
#' @param d1 Path to first <umccrised/sample> directory.
#' @param d2 Path to second <umccrised/sample> directory.
#' @param sample Sample name.
#' @return A tibble with the following columns:
#'   - sample name
#'   - variant type (e.g. SNV, SV, CNV)
#'   - file label (e.g. pcgr, cpsr, purple etc.)
#'   - run1 file path
#'   - run2 file path
#'
#' @examples
#' \dontrun{
#' um1 <- "path/to/umccrised/sample1"
#' um2 <- "path/to/umccrised/sample2"
#' merge_umccrise_outputs(um1, um2)
#' }
#' @export
merge_umccrise_outputs <- function(d1, d2, sample) {

  um1 <- umccrise_outputs(d1)
  um2 <- umccrise_outputs(d2)

  dplyr::inner_join(um1, um2, by = c("flabel", "vartype")) %>%
    dplyr::filter(!.data$vartype == "IGNORE_ME") %>%
    dplyr::mutate(sample_nm = sample) %>%
    dplyr::select(.data$sample_nm, .data$vartype, .data$flabel, .data$fpath.x, .data$fpath.y) %>%
    utils::write.table(file = "", quote = FALSE, sep = "\t", row.names = FALSE, col.names = FALSE)
}


#' Read YAML configs from two bcbio runs
#'
#' Generates a list containing absolute paths to variant files for
#' two bcbio runs.
#'
#'
#' @param conf1 Path to `final/config/<timestamp>_project.yaml` for run1.
#' @param conf2 Path to `final/config/<timestamp>_project.yaml` for run2.
#' @return A list with the following elements:
#'   - 'batch_name', 'tumor_name', 'normal_name': batch/tumor/normal names.
#'   - 'variant_files': file type. Can be one of:
#'     1. ensemble_som
#'     2. mutect2_som
#'     3. strelka2_som
#'     4. vardict_som
#'     5. ensemble_ger
#'     6. gatk-haplotype_ger
#'     7. strelka2_ger
#'     8. vardict_ger
#'     9. manta_som-sv
#'
#' @examples
#' \dontrun{
#' conf1 <- "path/to/bcbio_run1/final/config/<timestamp>_project.yaml"
#' conf2 <- "path/to/bcbio_run2/final/config/<timestamp>_project.yaml"
#' read_bcbio_configs(conf1, conf2)
#' }
#' @export
read_bcbio_configs <- function(conf1, conf2) {
  b1 <- read_bcbio_config(conf1)
  b2 <- read_bcbio_config(conf2)

  ### variant callers
  vc1 <- b1$varcallers
  vc2 <- b2$varcallers
  stopifnot(all(vc1$caller_name2 == vc2$caller_name2))

  caller_nms <- unique(vc1$caller_name2)
  caller_list <- purrr::map(caller_nms, function(caller) {
    list(run1 = vc1$fpath[vc1$caller_name2 == caller],
         run2 = vc2$fpath[vc2$caller_name2 == caller])}) %>%
    purrr::set_names(caller_nms)

  ### check stuff: aligner + genome_build can differ
  stopifnot(b1$batch_name == b2$batch_name,
            b1$tumor_name == b2$tumor_name,
            b1$normal_name == b2$normal_name,
            b1$analysis_type == b2$analysis_type)

  out <- list(
    batch_name = b1$batch_name,
    tumor_name = b1$tumor_name,
    normal_name = b1$normal_name,
    aligner = list(run1 = b1$aligner,
                   run2 = b2$aligner),
    genome_build = list(run1 = b1$genome_build,
                        run2 = b2$genome_build),
    analysis_type = b1$analysis_type,
    variant_files = caller_list)

  out

}

#' Read SNV count file output by woof
#'
#' Reads SNV count file output by woof
#'
#' @param x Path to file with counts
#' @return A single integer
#'
#' @examples
#'
#' x <- system.file("extdata", "snv/count_vars.txt", package = "woofr")
#' read_snv_count_file(x)
#'
#' @export
read_snv_count_file <- function(x) {
  column_nms <- c("sample", "flabel", "count")
  if (!file.exists(x)) {
    # return tibble of NAs
    res <- rep(NA, length(column_nms)) %>%
      purrr::set_names(column_nms) %>%
      as.list() %>%
      dplyr::as_tibble()

    return(res)
  }
  res <- readr::read_tsv(x, col_types = "cci")
  stopifnot(names(res) == column_nms)
  res
}

#' Read SNV eval file output by woof
#'
#' Reads SNV eval file output by woof
#'
#' @param x Path to file with eval results
#' @return A tibble with a single row of evaluation metrics
#'
#' @examples
#'
#' x <- system.file("extdata", "snv/eval_stats.tsv", package = "woofr")
#' read_snv_eval_file(x)
#'
#' @export
read_snv_eval_file <- function(x) {
  column_nms <- c("sample", "flabel", "subset",
                  "SNP_Truth", "SNP_TP", "SNP_FP", "SNP_FN", "SNP_Recall", "SNP_Precision",
                  "SNP_f1", "SNP_f2", "SNP_f3", "IND_Truth", "IND_TP", "IND_FP",
                  "IND_FN", "IND_Recall", "IND_Precision", "IND_f1", "IND_f2", "IND_f3")
  if (!file.exists(x)) {
    # return tibble of NAs
    res <- rep(NA, length(column_nms)) %>%
      purrr::set_names(column_nms) %>%
      as.list() %>%
      dplyr::as_tibble()

    return(res)
  }
  res <- readr::read_tsv(x, col_types = readr::cols(
    .default = "d", sample = "c", flabel = "c", subset = "c"))
  stopifnot(names(res) == column_nms)
  res
}

#' Read SV FP/FN file output by woof
#'
#' Reads SV FP/FN file output by woof
#'
#' @param x Path to file with FP/FN variants
#' @return A tibble containing FP/FN SV variants
#'
#' @examples
#'
#' x <- system.file("extdata", "sv/fpfn.tsv", package = "woofr")
#' read_sv_fpfn_file(x)
#'
#' @export
read_sv_fpfn_file <- function(x) {
  column_nms <- c("FP_or_FN", "sample", "flabel", "chrom1","pos1", "chrom2", "pos2", "svtype")
  if (!file.exists(x)) {
    res <- rep(NA, length(column_nms)) %>%
      purrr::set_names(column_nms) %>%
      as.list() %>%
      dplyr::as_tibble()
    return(res)
  }
  res <- readr::read_tsv(x, col_types = "ccccicic")
  stopifnot(names(res) == column_nms)
  res
}

#' Read SV eval metrics file output by woof
#'
#' Reads SV eval metrics file output by woof
#'
#' @param x Path to file with SV evaluation metrics
#' @return A tibble with a single row of evaluation metrics
#'
#' @examples
#'
#' x <- system.file("extdata", "sv/eval_metrics.tsv", package = "woofr")
#' read_sv_eval_file(x)
#'
#' @export
read_sv_eval_file <- function(x) {
  column_nms <- c("sample", "flabel", "run1_count", "run2_count", "Recall",
                  "Precision", "Truth", "TP", "FP", "FN")
  if (!file.exists(x)) {
    res <- rep(NA, length(column_nms)) %>%
      purrr::set_names(column_nms) %>%
      as.list() %>%
      dplyr::as_tibble()
    return(res)
  }
  res <- readr::read_tsv(x, col_types = "cciiddiiii")
  stopifnot(names(res) == column_nms)
  res
}


#' Intersect two Manta VCF files
#'
#' Intersects two Manta VCF files for evaluation.
#'
#' @param f1 Path to first Manta file
#' @param f2 Path to second ('truthset') Manta file
#' @param samplename Sample name (used for labelling).
#' @param flab File name (used for labelling).
#' @param bnd_switch Logical. Switch BND pairs for more matches (default: TRUE).
#' @return A list with the following elements:
#'   - tot_vars: total variants for file1 and file2
#'   - fp: tibble with False Positive calls i.e. variants in f1 that are not in f2
#'   - fn: tibble with False Negative calls i.e. variants in f2 that are not in f1
#'
#' @examples
#'
#' \dontrun{
#' f1 <- "path/to/run1/manta.vcf.gz"
#' f2 <- "path/to/run2/manta.vcf.gz"
#' mi <- manta_isec(f1, f2)
#' }
#'
#' @export
manta_isec <- function(f1, f2, samplename, flab, bnd_switch = TRUE) {

  read_manta_both <- function(f1, f2) {
    vcf1 <- rock::prep_manta_vcf(f1, filter_pass = TRUE)$sv
    vcf2 <- rock::prep_manta_vcf(f2, filter_pass = TRUE)$sv
    list(f1 = vcf1, f2 = vcf2)
  }

  switch_bnd <- function(d) {
    stopifnot(all(colnames(d) %in% c("chrom1", "pos1", "chrom2", "pos2", "svtype")))
    no_bnd <- dplyr::filter(d, !.data$svtype %in% "BND")
    bnd <-
      dplyr::filter(d, .data$svtype %in% "BND") %>%
      dplyr::select(chrom1 = .data$chrom2, pos1 = .data$pos2,
                    chrom2 = .data$chrom1, pos2 = .data$pos1, .data$svtype)

    dplyr::bind_rows(no_bnd, bnd)
  }

  mb <- read_manta_both(f1, f2)
  tot_vars <- list(run1 = nrow(mb$f1), run2 = nrow(mb$f2))
  col_nms <- colnames(mb$f1)
  fp <- dplyr::anti_join(mb$f1, mb$f2, by = col_nms)
  fn <- dplyr::anti_join(mb$f2, mb$f1, by = col_nms)

  if (bnd_switch) {
    # some real matching cases simply have switched BND mates
    fp_new <- dplyr::anti_join(switch_bnd(fp), fn, by = col_nms) %>% switch_bnd()
    fn_new <- dplyr::anti_join(switch_bnd(fn), fp, by = col_nms) %>% switch_bnd()
    fp <- fp_new
    fn <- fn_new
  }

  fp <- fp %>%
    dplyr::mutate(sample = samplename, flabel = flab) %>%
    dplyr::select(.data$sample, .data$flabel, dplyr::everything())
  fn <- fn %>%
    dplyr::mutate(sample = samplename, flabel = flab) %>%
    dplyr::select(.data$sample, .data$flabel, dplyr::everything())

  return(list(tot_vars = tot_vars,
              fp = fp,
              fn = fn))
}

#' Manta Comparison Metrics
#'
#' Returns evaluation metrics from comparing two Manta call sets.
#'
#' @param mi Output from \code{\link{manta_isec}}.
#' @param samplename Sample name (used for labelling).
#' @param flab File name (used for labelling).
#' @return A single row tibble with the following columns:
#'   - sample: samplename
#'   - flabel: flab
#'   - run1_count: total variants in first file
#'   - run2_count: total variants in second file
#'   - TP: in first and second
#'   - FP: in first but not second
#'   - FN: in second but not first
#'   - Recall: TP / (TP + FN)
#'   - Precision: TP / (TP + FP)
#'   - Truth: TP + FN
#'
#' @examples
#'
#' \dontrun{
#' f1 <- "path/to/run1/manta.vcf.gz"
#' f2 <- "path/to/run2/manta.vcf.gz"
#' mi <- manta_isec(f1, f2)
#' manta_isec_stats(mi, "sampleA", "manta1")
#' }
#'
#' @export
manta_isec_stats <- function(mi, samplename, flab) {
  fn <- nrow(mi$fn)
  fp <- nrow(mi$fp)
  tp <- mi$tot_vars$run2 - fn
  truth <- tp + fn
  recall <- tp / truth
  precision <- tp / (tp + fp)

  dplyr::tibble(
    sample = samplename, flabel = flab,
    run1_count = mi$tot_vars$run1, run2_count = mi$tot_vars$run2,
    Recall = round(recall, 3), Precision = round(precision, 3), Truth = truth,
    TP = tp, FP = fp, FN = fn
  )
}

#' Get Manta Circos with FP/FN calls
#'
#' Returns Circos plot highlighting FP/FN calls from a Manta comparison.
#'
#' @param mi Output from \code{\link{manta_isec}}.
#' @param samplename Sample name (used for labelling).
#' @param outdir Directory to write circos to.
#' @return Path to circos plot highlighting FP (green) and FN (red) calls from a
#'   Manta comparison.
#'
#' @examples
#'
#' \dontrun{
#' f1 <- "path/to/run1/manta.vcf.gz"
#' f2 <- "path/to/run2/manta.vcf.gz"
#' mi <- manta_isec(f1, f2)
#' get_circos(mi, "sampleA", "outdir1")
#' }
#'
#' @export
get_circos <- function(mi, samplename, outdir) {

  prep_svs_circos <- function() {
    sv <- dplyr::bind_rows(list(fp = mi$fp, fn = mi$fn), .id = "fp_or_fn")
    links_coloured <- sv %>%
      dplyr::mutate(
        chrom1 = paste0("hs", .data$chrom1),
        chrom2 = paste0("hs", .data$chrom2),
        col = dplyr::case_when(
          fp_or_fn == "fp" ~ '(0,255,0)',
          fp_or_fn == "fn" ~ '(255,0,0)',
          TRUE ~ 'Oops'),
        pos1b = .data$pos1,
        pos2b = .data$pos2,
        col = paste0('color=', col)) %>%
      dplyr::select(.data$chrom1, .data$pos1, .data$pos1b, .data$chrom2, .data$pos2, .data$pos2b, .data$col)

    return(links_coloured)
  }

  write_circos_configs <- function() {
    dir.create(outdir, recursive = TRUE)
    links <- prep_svs_circos()
    message(glue::glue("Writing circos links file to '{outdir}'."))
    readr::write_tsv(links, file.path(outdir, "SAMPLE.link.circos"), col_names = FALSE)

    message(glue::glue("Copying circos templates to '{outdir}'"))
    file.copy(system.file("templates/circos/hg38/circos_sv.conf", package = "pebbles"),
              file.path(outdir, "circos.conf"), overwrite = TRUE)
    file.copy(system.file("templates/circos/hg38/gaps.txt", package = "pebbles"),
              outdir, overwrite = TRUE)
    file.copy(system.file("templates/circos/hg38/ideogram.conf", package = "pebbles"),
              outdir, overwrite = TRUE)
  }

  run_circos <- function() {
    circos_png <- glue::glue("circos_{samplename}.png")
    cmd <- glue::glue("echo '$(date) running circos on {samplename}' && circos -nosvg -conf {outdir}/circos.conf -outputdir {outdir} -outputfile {circos_png}")

    if (Sys.which("circos") != "") {
      system(cmd, ignore.stdout = TRUE)
      return(circos_png)
    } else {
      stop("Can't find 'circos' in your PATH. Exiting.")
    }
  }

  write_circos_configs()
  circos_png <- run_circos()
  circos_png
}


#' Read PURPLE gene segments
#'
#' Reads the gene.cnv file output by PURPLE
#'
#' @param x Path to PURPLE `gene.cnv` (or `cnv.gene.tsv`) file.
#' @return A tibble with the main columns of interest from the PURPLE `gene.cnv` file i.e.
#'   chrom, start, end, gene, min_cn and max_cn.
#'
#' @examples
#'
#' x <- system.file("extdata", "cnv/sample_A.purple.gene.cnv", package = "woofr")
#' y <- system.file("extdata", "cnv/sample_B.purple.cnv.gene.tsv", package = "woofr")
#' read_purple_gene_file(x)
#' read_purple_gene_file(y)
#'
#' @export
read_purple_gene_file <- function(x) {
  column_nms <- c("chromosome", "start", "end", "gene", "mincopynumber", "maxcopynumber")
  d <- readr::read_tsv(x, col_types = readr::cols(.default = "c")) %>%
    dplyr::select(1:6)
  names(d) <- tolower(names(d))
  stopifnot(names(d) == column_nms)
  d %>%
    dplyr::mutate(
      start = as.integer(.data$start),
      end = as.integer(.data$end),
      min_cn = round(as.numeric(.data$mincopynumber), 1),
      max_cn = round(as.numeric(.data$maxcopynumber), 1)) %>%
    dplyr::select(
      chrom = .data$chromosome, .data$start, .data$end,.data$gene, .data$min_cn, .data$max_cn)
}

#' Compare two PURPLE gene CNV files
#'
#' Compares two PURPLE `gene.cnv` (or `cnv.gene.tsv`) files.
#'
#' @param cnv1 Path to first PURPLE `gene.cnv` (or `cnv.gene.tsv`) file.
#' @param cnv2 Path to second PURPLE `gene.cnv` (or `cnv.gene.tsv`) file ('TRUTHSET').
#' @param out_cn_diff Path to write genes with copy number differences between
#'   the two runs - needs to be a writable directory.
#' @param out_coord_diff Path to write genes with different coordinates between
#'   the two runs - needs to be a writable directory.
#' @param threshold Numeric. Copy number differences smaller than this value are not reported.
#' @return Writes results from the comparison to `out_cn_diff` and `out_coord_diff`.
#'
#'
#' @examples
#'
#' cnv1 <- system.file("extdata", "cnv/sample_A.purple.gene.cnv", package = "woofr")
#' cnv2 <- system.file("extdata", "cnv/sample_B.purple.cnv.gene.tsv", package = "woofr")
#' out1 <- tempfile()
#' out2 <- tempfile()
#' compare_purple_gene_files(cnv1, cnv2, out1, out2, threshold = 0.1)
#'
#' @export
compare_purple_gene_files <- function(cnv1, cnv2, out_cn_diff, out_coord_diff, threshold = 0.1) {
  stopifnot(is.numeric(threshold), threshold >= 0, length(threshold) == 1)

  x1 <- read_purple_gene_file(cnv1)
  x2 <- read_purple_gene_file(cnv2)
  # compare chrom,start,end,gene
  coord_diff <-
    dplyr::bind_rows(
      fp = dplyr::anti_join(x1, x2, by = c("chrom", "start", "end", "gene")),
      fn = dplyr::anti_join(x2, x1, by = c("chrom", "start", "end", "gene")),
      .id = "fp_or_fn")

  # compare min/max cn
  cn_diff <-
    dplyr::left_join(x1, x2, by = c("chrom", "start", "end", "gene"), suffix = paste0(".run", 1:2)) %>%
    dplyr::mutate(min_diff = abs(.data$min_cn.run1 - .data$min_cn.run2) > threshold,
                  max_diff = abs(.data$max_cn.run1 - .data$max_cn.run2) > threshold) %>%
    dplyr::filter(.data$min_diff | .data$max_diff)

  utils::write.table(cn_diff, file = out_cn_diff, quote = FALSE, sep = "\t", row.names = FALSE, col.names = TRUE)
  utils::write.table(coord_diff, file = out_coord_diff, quote = FALSE, sep = "\t", row.names = FALSE, col.names = TRUE)
}

#' Check Comparison Input File
#'
#' Checks that the input file is suitable for running 'woof compare'.
#'
#' @param x Path to tab-separated comparison input file.
#'       Must contain the following five fields per file (NOTE: do not include column names):
#'       sample name, variant type (SNV, SV or CNV), file label, run1 & run2 file paths (can be S3 paths).
#' @return If the file has issues, an error message. If there
#' are no issues, simply returns file path.
#'
#' @examples
#' \dontrun{
#' x <- "path/to/cromwell_inputs.tsv"
#' check_comparison_input(x)
#' }
#' @export
check_comparison_input <- function(x) {
  d <- readr::read_tsv(x, col_types = readr::cols(.default = "c"),
                       col_names = c("sample", "vartype", "flabel", "run1", "run2"))
  assertthat::assert_that(
    all(d$vartype %in% c("SNV", "SV", "CNV")),
    all(startsWith(d$run1, "/") | startsWith(d$run1, "s3")),
    all(startsWith(d$run2, "/") | startsWith(d$run2, "s3"))
  )

  x
}
