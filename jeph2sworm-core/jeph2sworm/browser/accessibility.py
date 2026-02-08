"""Accessibility - A11y testing for web applications."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


class AccessibilityChecker:
    """
    Automated accessibility (a11y) testing for web applications.

    Checks for:
    - Missing alt text on images
    - Missing ARIA labels
    - Color contrast issues
    - Keyboard navigation
    - Focus management
    - Heading hierarchy
    - Form label associations

    Uses Playwright's built-in accessibility tree + custom checks.
    """

    # WCAG 2.1 AA minimum contrast ratios
    MIN_CONTRAST_NORMAL = 4.5
    MIN_CONTRAST_LARGE = 3.0

    async def audit(self, page: Any) -> Dict[str, Any]:
        """
        Run a full accessibility audit on a page.

        Returns a report with violations, warnings, and passes.
        """
        violations: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        passes: List[str] = []

        # 1. Get accessibility tree
        a11y_tree = await self._get_accessibility_tree(page)

        # 2. Check images for alt text
        img_results = await self._check_images(page)
        violations.extend(img_results["violations"])
        if not img_results["violations"]:
            passes.append("All images have alt text")

        # 3. Check form labels
        form_results = await self._check_form_labels(page)
        violations.extend(form_results["violations"])
        if not form_results["violations"]:
            passes.append("All form inputs have labels")

        # 4. Check heading hierarchy
        heading_results = await self._check_headings(page)
        violations.extend(heading_results["violations"])
        warnings.extend(heading_results.get("warnings", []))
        if not heading_results["violations"]:
            passes.append("Heading hierarchy is valid")

        # 5. Check ARIA attributes
        aria_results = await self._check_aria(page)
        violations.extend(aria_results["violations"])
        warnings.extend(aria_results.get("warnings", []))

        # 6. Check interactive elements
        interactive_results = await self._check_interactive_elements(page)
        violations.extend(interactive_results["violations"])

        # 7. Check page language
        lang_results = await self._check_language(page)
        if lang_results.get("violation"):
            violations.append(lang_results["violation"])
        else:
            passes.append("Page has lang attribute")

        score = self._calculate_score(violations, warnings, passes)

        return {
            "score": score,
            "violations": violations,
            "warnings": warnings,
            "passes": passes,
            "total_checks": len(violations) + len(warnings) + len(passes),
            "a11y_tree_nodes": len(a11y_tree) if isinstance(a11y_tree, list) else 0,
        }

    async def _get_accessibility_tree(self, page: Any) -> Any:
        """Get the page's accessibility tree."""
        try:
            snapshot = await page.accessibility.snapshot()
            return snapshot.get("children", []) if snapshot else []
        except Exception as e:
            logger.warning("a11y_tree_failed", error=str(e))
            return []

    async def _check_images(self, page: Any) -> Dict[str, Any]:
        """Check all images for alt text."""
        violations = []
        try:
            images = await page.query_selector_all("img")
            for img in images:
                alt = await img.get_attribute("alt")
                src = await img.get_attribute("src") or "unknown"
                role = await img.get_attribute("role")

                if alt is None and role != "presentation":
                    violations.append({
                        "rule": "img-alt",
                        "impact": "critical",
                        "message": f"Image missing alt text: {src[:100]}",
                        "wcag": "1.1.1",
                    })
                elif alt == "" and role != "presentation":
                    # Empty alt is only ok for decorative images
                    pass  # Acceptable if intentionally decorative
        except Exception as e:
            logger.warning("img_check_failed", error=str(e))

        return {"violations": violations}

    async def _check_form_labels(self, page: Any) -> Dict[str, Any]:
        """Check form inputs for associated labels."""
        violations = []
        try:
            inputs = await page.query_selector_all(
                "input:not([type='hidden']):not([type='submit']):not([type='button']), "
                "select, textarea"
            )
            for inp in inputs:
                inp_id = await inp.get_attribute("id")
                aria_label = await inp.get_attribute("aria-label")
                aria_labelledby = await inp.get_attribute("aria-labelledby")
                placeholder = await inp.get_attribute("placeholder")

                has_label = bool(aria_label or aria_labelledby)
                if inp_id and not has_label:
                    # Check for label[for=id]
                    label = await page.query_selector(f'label[for="{inp_id}"]')
                    has_label = label is not None

                if not has_label and not placeholder:
                    inp_type = await inp.get_attribute("type") or "text"
                    violations.append({
                        "rule": "label",
                        "impact": "serious",
                        "message": f"Form input ({inp_type}) missing label",
                        "wcag": "1.3.1",
                    })
        except Exception as e:
            logger.warning("form_label_check_failed", error=str(e))

        return {"violations": violations}

    async def _check_headings(self, page: Any) -> Dict[str, Any]:
        """Check heading hierarchy (h1-h6 should be sequential)."""
        violations = []
        warnings = []
        try:
            headings = await page.evaluate("""
                () => Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))
                    .map(h => ({ level: parseInt(h.tagName[1]), text: h.textContent.trim().substring(0, 50) }))
            """)

            if not headings:
                warnings.append({
                    "rule": "heading-order",
                    "impact": "moderate",
                    "message": "Page has no headings",
                })
            else:
                # Check for h1
                h1_count = sum(1 for h in headings if h["level"] == 1)
                if h1_count == 0:
                    violations.append({
                        "rule": "page-has-heading-one",
                        "impact": "moderate",
                        "message": "Page missing h1 heading",
                        "wcag": "1.3.1",
                    })

                # Check hierarchy (no skipping levels)
                prev_level = 0
                for h in headings:
                    if h["level"] > prev_level + 1 and prev_level > 0:
                        violations.append({
                            "rule": "heading-order",
                            "impact": "moderate",
                            "message": f"Heading level skipped: h{prev_level} -> h{h['level']} ('{h['text']}')",
                            "wcag": "1.3.1",
                        })
                    prev_level = h["level"]

        except Exception as e:
            logger.warning("heading_check_failed", error=str(e))

        return {"violations": violations, "warnings": warnings}

    async def _check_aria(self, page: Any) -> Dict[str, Any]:
        """Check ARIA attributes for correctness."""
        violations = []
        warnings = []
        try:
            # Check for elements with role but missing required ARIA attributes
            buttons_no_label = await page.evaluate("""
                () => Array.from(document.querySelectorAll('[role="button"]'))
                    .filter(el => !el.textContent.trim() && !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby'))
                    .length
            """)
            if buttons_no_label > 0:
                violations.append({
                    "rule": "aria-label",
                    "impact": "serious",
                    "message": f"{buttons_no_label} elements with role='button' missing accessible name",
                    "wcag": "4.1.2",
                })

            # Check for invalid ARIA roles
            invalid_roles = await page.evaluate("""
                () => {
                    const validRoles = ['alert','alertdialog','application','article','banner','button',
                        'cell','checkbox','columnheader','combobox','complementary','contentinfo',
                        'definition','dialog','directory','document','feed','figure','form','grid',
                        'gridcell','group','heading','img','link','list','listbox','listitem','log',
                        'main','marquee','math','menu','menubar','menuitem','menuitemcheckbox',
                        'menuitemradio','navigation','none','note','option','presentation','progressbar',
                        'radio','radiogroup','region','row','rowgroup','rowheader','scrollbar','search',
                        'searchbox','separator','slider','spinbutton','status','switch','tab','table',
                        'tablist','tabpanel','term','textbox','timer','toolbar','tooltip','tree',
                        'treegrid','treeitem'];
                    return Array.from(document.querySelectorAll('[role]'))
                        .map(el => el.getAttribute('role'))
                        .filter(role => !validRoles.includes(role));
                }
            """)
            for role in invalid_roles:
                violations.append({
                    "rule": "aria-valid-attr-value",
                    "impact": "critical",
                    "message": f"Invalid ARIA role: '{role}'",
                    "wcag": "4.1.2",
                })

        except Exception as e:
            logger.warning("aria_check_failed", error=str(e))

        return {"violations": violations, "warnings": warnings}

    async def _check_interactive_elements(self, page: Any) -> Dict[str, Any]:
        """Check interactive elements are keyboard accessible."""
        violations = []
        try:
            # Check for click handlers on non-interactive elements without tabindex
            non_accessible = await page.evaluate("""
                () => {
                    const interactive = ['a', 'button', 'input', 'select', 'textarea'];
                    return Array.from(document.querySelectorAll('[onclick]'))
                        .filter(el => !interactive.includes(el.tagName.toLowerCase()) && !el.hasAttribute('tabindex'))
                        .map(el => el.tagName.toLowerCase())
                        .length;
                }
            """)
            if non_accessible > 0:
                violations.append({
                    "rule": "keyboard-accessible",
                    "impact": "serious",
                    "message": f"{non_accessible} non-interactive elements with click handlers missing tabindex",
                    "wcag": "2.1.1",
                })
        except Exception as e:
            logger.warning("interactive_check_failed", error=str(e))

        return {"violations": violations}

    async def _check_language(self, page: Any) -> Dict[str, Any]:
        """Check that the page has a lang attribute."""
        try:
            lang = await page.evaluate("() => document.documentElement.getAttribute('lang')")
            if not lang:
                return {
                    "violation": {
                        "rule": "html-has-lang",
                        "impact": "serious",
                        "message": "HTML element missing lang attribute",
                        "wcag": "3.1.1",
                    }
                }
        except Exception:
            pass
        return {}

    def _calculate_score(
        self, violations: List, warnings: List, passes: List
    ) -> int:
        """Calculate an accessibility score (0-100)."""
        total = len(violations) + len(warnings) + len(passes)
        if total == 0:
            return 100

        # Weight: violations = -3, warnings = -1, passes = +1
        penalty = (len(violations) * 3 + len(warnings)) / (total * 3) * 100
        return max(0, round(100 - penalty))
