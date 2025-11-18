import React from "react";
import "./SearchBar.css";
import { FiSearch } from "react-icons/fi";

export default function SearchBar({
    value,
    onChange,
    onSearch,
    placeholder = "Ask me about history…"
}) {
    const handleKeyDown = (e) => {
        if (e.key === "Enter" || e.key === ":") {
            onSearch?.(value);
        }
    };

    const handleIconClick = () => {
        onSearch?.(value);
    };

    return (
        <div className="searchbar-wrapper">
            <FiSearch className="searchbar-icon" onClick={handleIconClick} />
            <input
                className="searchbar-input"
                type="text"
                value={value}
                onChange={(e) => onChange?.(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={placeholder}
            />
        </div>
    );
}
