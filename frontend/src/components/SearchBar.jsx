import React from "react";
import "./SearchBar.css";
import { FiSearch } from "react-icons/fi"; // search icon

export default function SearchBar({
    value,
    onChange,
    placeholder = "Ask me about history…"
}) {
    return (
        <div className="searchbar-wrapper">
            <FiSearch className="searchbar-icon" />
            <input
                className="searchbar-input"
                type="text"
                value={value}
                onChange={(e) => onChange?.(e.target.value)}
                placeholder={placeholder}
            />
        </div>
    );
}
